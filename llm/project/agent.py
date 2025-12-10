import json
import requests
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import contextvars
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
from formatter import ResponseFormatter
import config


# Context storage for the auth token
request_token = contextvars.ContextVar("request_token", default=None)


def execute_graphql(query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute a GraphQL query."""
    try:
        # Auto-fix: Replace single quotes with double quotes for GraphQL spec compliance
        if query:
            query = query.replace("'", '"')

        headers = {"Content-Type": "application/json"}
        token = request_token.get()
        if token:
            headers["Authorization"] = token

        response = requests.post(
            config.GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30,
        )

        # Handle HTTP errors but try to get GraphQL error details first
        if response.status_code != 200:
            try:
                error_body = response.json()
                if "errors" in error_body:
                    return {
                        "error": "GraphQL Validation Error",
                        "details": error_body["errors"],
                        "query": query,
                    }
            except:
                pass  # Fallback to raising status

        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            return {
                "error": "GraphQL Execution Error",
                "details": result["errors"],
                "query": query,
            }

        return result
    except Exception as e:
        return {"error": str(e), "query": query}


@tool
def graphql_query(query: str) -> str:
    """
    Execute a GraphQL query against the inventory/supplier database.
    Use this for: Inventory items, stock levels, suppliers, item details.

    CRITICAL RULES:
    1. ALL queries MUST start with the 'query' keyword!
    2. USE SINGLE QUOTES for all string arguments.
    3. DO NOT GUESS FIELDS. Only use the fields listed below.
    4. NO 'where' CLAUSE! Filter directly on arguments.

    AVAILABLE QUERIES:
    - allInventory(filters): Get inventory items
    - allSuppliers(filters): Get suppliers

    INVENTORY FILTERS (Direct Arguments):
    - itemName: 'text' - partial match
    - supplierName: 'text' - partial match
    - minPrice, maxPrice: number
    - minQuantity, maxQuantity: number
    - isActive: true/false
    - type: 'category'
    - userEmail: 'email' - CRITICAL: Always use this to filter by current user

    EXAMPLES - COPY THESE EXACTLY:

    1. INVENTORY REPORT:
       query { allInventory { edges { node { id itemName quantity sellingPrice supplier } } } }

    2. Search specific item:
       query { allInventory(itemName: 'Coffee') { edges { node { id itemName quantity } } } }

    3. Low stock:
       query { allInventory(maxQuantity: 10) { edges { node { id itemName quantity } } } }

    4. All suppliers:
       query { allSuppliers { edges { node { id supplierName contactPerson } } } }

    AVAILABLE INVENTORY FIELDS:
    id, itemName, description, type, quantity, quantityUnit, costPrice, sellingPrice,
    minQuantity, isActive, autoReorder, supplier, lastRestockDate

    AVAILABLE SUPPLIER FIELDS:
    id, supplierName, contactPerson, supplierEmail, supplierPhone

    Args:
        query: Complete GraphQL query starting with 'query'
    """
    try:
        with open("debug_agent.txt", "a") as f:
            f.write(f"Query: {query}\n")
    except:
        pass

    result = execute_graphql(query)
    return json.dumps(result, indent=2)


@tool
def sales_query(query: str) -> str:
    """
    Execute a GraphQL query against the SALES database.
    Use this for: Sales transactions, revenue reports, top selling items.

    CRITICAL RULES:
    1. ALL queries MUST start with the 'query' keyword!
    2. USE SINGLE QUOTES for all string arguments.
    3. DO NOT GUESS FIELDS. Only use the fields listed below.
    4. NO 'where' CLAUSE! Filter directly on arguments.
    5. NEVER use a 'filters' argument. Pass filters directly (e.g. productName: 'Coffee').

    AVAILABLE QUERIES:
    - allSales(productName: '...', minRevenue: 100, ...): Get raw sales transactions
    - salesReport(groupBy, dateFrom, dateTo, userEmail): Get aggregated reports

    AVAILABLE ARGUMENTS (for allSales):
    - productName: 'text' (CRITICAL: Use 'productName', NOT 'itemName' for sales!)
    - salesUid: 'text'
    - weatherCondition: 'text'
    - minQuantity, maxQuantity: number
    - minRevenue, maxRevenue: number
    - saleDateAfter, saleDateBefore: 'YYYY-MM-DD' (STRICT ISO FORMAT REQUIRED)
    - wasOnSale: true/false
    - userEmail: 'email' - CRITICAL: Always use this to filter by current user
    - orderBy: 'sale_date', '-revenue', etc

    EXAMPLES - COPY THESE EXACTLY:

    1. SALES OVERVIEW:
       query { allSales(first: 50) { edges { node { id saleDate revenue quantitySold } } } }

    2. REVENUE TRENDS (Aggregated) - USE STRICT DATES:
       query { salesReport(groupBy: "date", dateFrom: "2025-01-01", dateTo: "2025-12-31", userEmail: '...') { date totalRevenue } }

    3. TOP SELLING PRODUCTS (Aggregated):
       query { salesReport(groupBy: "product", dateFrom: "2025-01-01", dateTo: "2025-12-31", userEmail: '...') { name totalRevenue totalQuantity } }

    4. FILTER BY DATE & WEATHER:
       query { allSales(saleDateAfter: '2023-01-01', weatherCondition: 'Sunny') { edges { node { saleDate revenue } } } }

    5. SALES REPORT PER ITEM (Aggregated):
       query { salesReport(groupBy: "product", userEmail: '...') { name totalRevenue totalQuantity } }

    AVAILABLE FIELDS (allSales):
    id, salesUid, saleDate, quantitySold, revenue, revenuePerUnit,
    weatherTemperature, weatherCondition, wasOnSale, promotionType, discountPercentage,
    prodId { itemName, category, costPrice, sellingPrice },
    holidays { edges { node { name date } } }

    Args:
        query: Complete GraphQL query starting with 'query'
    """
    try:
        with open("debug_agent.txt", "a") as f:
            f.write(f"Query: {query}\n")
    except:
        pass

    result = execute_graphql(query)
    return json.dumps(result, indent=2)


@tool
def predict_sales(item_name: str, days: int = 7) -> str:
    """
    Predict future sales for a specific item using the PatchTST model.

    Args:
        item_name: Name of the product (e.g. 'Coffee Beans')
        days: Number of days to predict (default 7)
    """
    # 1. Find Product ID
    search_query = f"query {{ allInventory(itemName: '{item_name}') {{ edges {{ node {{ id itemName quantity }} }} }} }}"
    search_result = execute_graphql(search_query)

    # Extract ID
    try:
        if "data" not in search_result or "allInventory" not in search_result["data"]:
            return json.dumps({"error": f"Could not find product '{item_name}'"})

        edges = search_result["data"]["allInventory"]["edges"]
        if not edges:
            return json.dumps({"error": f"Product '{item_name}' not found."})
        product_id = edges[0]["node"]["id"]
        real_name = edges[0]["node"]["itemName"]
        current_quantity = edges[0]["node"].get("quantity", 0)
    except Exception as e:
        return json.dumps({"error": f"Failed to resolve product ID: {str(e)}"})

    # 2. Call Prediction API
    try:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)

        payload = {
            "business_id": "biz_001",  # Default for demo
            "begin_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "item_ids": [product_id],
        }

        # Prediction Service URL (assuming port 8080 based on prediction_model/app.py)
        url = "http://localhost:8080/predict"
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Return structured data
            return json.dumps(
                {
                    "type": "prediction",
                    "product": real_name,
                    "current_inventory": current_quantity,
                    "forecast": data["forecast"],
                    "disclaimer": "This is an AI prediction and may vary from actual results.",
                },
                indent=2,
            )
        else:
            return json.dumps({"error": f"Prediction service error: {response.text}"})

    except Exception as e:
        return json.dumps(
            {
                "error": f"Prediction failed: {str(e)}. Is the prediction service running?"
            }
        )


@tool
def train_model() -> str:
    """
    Trigger the training of the sales prediction model using the latest data.
    Use this when the user asks to "train the model", "retrain", or "update predictions".
    """
    try:
        url = f"{config.DJANGO_API_URL}sales/train/"
        response = requests.post(url, timeout=60)

        if response.status_code == 200:
            return json.dumps(
                {
                    "status": "success",
                    "message": "Model training started successfully. It may take a few moments to complete.",
                }
            )
        else:
            return json.dumps({"error": f"Training failed: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Error triggering training: {str(e)}"})


class GraphQLAgent:
    """Agent with GraphQL tool and response formatting."""

    def __init__(self):
        self.llm = ChatOllama(model=config.OLLAMA_MODEL, temperature=0.1)
        self.tools = [graphql_query, sales_query, predict_sales, train_model]
        self.tool_map = {t.name: t for t in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.conversation_history = {}

    def clear_history(self, session_id: str):
        """Clear the history for a given session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]

        # Also clear from DB if needed
        try:
            url = f"{config.DJANGO_API_URL}chat/history/{session_id}/"
            requests.delete(url, timeout=5)
        except Exception as e:
            print(f"Error clearing DB history: {e}")

    def _fetch_history_from_db(self, session_id: str):
        """Fetch chat history from Django API."""
        try:
            url = f"{config.DJANGO_API_URL}chat/history/{session_id}/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                messages = []

                # Always start with system message
                messages.append(self._get_system_message(session_id))

                for msg in data.get("messages", []):
                    role = msg["role"]
                    content = msg["content"]
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))

                self.conversation_history[session_id] = messages
        except Exception as e:
            print(f"Error fetching history: {e}")
            self.conversation_history[session_id] = []

    def _get_system_message(self, session_id: str) -> SystemMessage:
        current_date = datetime.now().strftime("%Y-%m-%d")
        user_email_instruction = (
            f" Your User Email is '{session_id}'. You MUST filter all 'allInventory' and 'allSales' queries by this email using (userEmail: '{session_id}')."
            if "@" in session_id
            else ""
        )

        return SystemMessage(
            content=(
                f"Current Date: {current_date}. "
                "You are BizAI, a smart business assistant. "
                "You answer questions based on real-time business data. "
                f"{user_email_instruction}"
                "\n\nTOOLS AVAILABLE:"
                "\n- 'graphql_query': For inventory and suppliers."
                "\n- 'sales_query': For sales, revenue, and transaction reports."
                "\n- 'predict_sales': For future sales forecasting."
                "\n- 'train_model': To retrain the AI model."
                "\n\nCRITICAL RESPONSE RULES (FOLLOW THESE OR YOU WILL BE TERMINATED):"
                "\n1. **NO JSON OR CODE**: You are FORBIDDEN from outputting JSON, code blocks, or technical identifiers in your final answer. The user is a business owner, not a developer."
                "\n2. **NO PLAY-BY-PLAY**: Do not say 'I received this JSON' or 'The object contains'. Just give the ANSWER."
                "\n3. **SUMMARIZE**: Interpret the data. Instead of listing 10 items, say 'You have 10 items, mostly Electronics.'."
                "\n4. If the user asks a general question, answer directly."
                "\n5. Use EMOJIS (📈, 💰, ✅) to make it friendly."
                "\n6. If a tool fails, just say 'I couldn't find that info right now' without technical details."
                "\n\nTOOL USAGE:"
                "\n- Always use SINGLE QUOTES inside GraphQL."
                "\n- Inventory Search: First `allInventory(itemName: '...')`, then use exact name for sales."
                "\n- Sales: Use `salesReport` for aggregates, `allSales` for lists."
            )
        )

    def _parse_tool_from_content(self, content: str) -> Optional[Dict]:
        """Attempt to parse a tool call from text content."""
        try:
            # Look for JSON block
            json_match = re.search(
                r'\{.*"name":.*"parameters":.*\}', content, re.DOTALL
            )
            if not json_match:
                # Try finding just the JSON object if it looks like a tool call
                json_match = re.search(r'\{.*"name":.*\}', content, re.DOTALL)

            if json_match:
                json_str = json_match.group(0)
                tool_data = json.loads(json_str)

                # Normalize format
                if "name" in tool_data:
                    name = tool_data["name"]
                    # Handle "parameters" vs "args"
                    args = tool_data.get("parameters", tool_data.get("args", {}))
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            pass
                    return {"name": name, "args": args, "id": "fallback_id"}
        except:
            pass
        return None

    def _save_to_db(
        self, session_id: str, role: str, content: str, formatted_data=None
    ):
        """Save message to Django API."""
        try:
            url = f"{config.DJANGO_API_URL}chat/history/{session_id}/"
            payload = {
                "role": role,
                "content": content,
                "formatted_data": formatted_data,
            }
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error saving to DB: {e}")

    def ask(self, user_query: str, session_id: str = "default") -> Dict[str, Any]:
        """Process user query and return formatted response."""

        if session_id not in self.conversation_history:
            self._fetch_history_from_db(session_id)

        messages = self.conversation_history[session_id]

        # 1. REFRESH SYSTEM MESSAGE (Update Date)
        # Always replace the first message (SystemMessage) with a fresh one containing current date
        if messages and isinstance(messages[0], SystemMessage):
            messages[0] = self._get_system_message(session_id)
        else:
            messages.insert(0, self._get_system_message(session_id))

        # Save user message
        self._save_to_db(session_id, "user", user_query)
        messages.append(HumanMessage(content=user_query))

        # Keep history manageable
        if len(messages) > 20:
            # Keep system message + last 19
            messages = [messages[0]] + messages[-19:]

        try:
            # Loop for tool execution (max 3 turns)
            max_turns = 3
            final_response = None
            formatted_data = None

            for _ in range(max_turns):
                response = self.llm_with_tools.invoke(messages)

                # Check for "fake" tool calls in content if tool_calls is empty
                fallback_tool_call = None
                if not response.tool_calls and response.content:
                    fallback_tool_call = self._parse_tool_from_content(response.content)
                    if fallback_tool_call:
                        # Convert to proper tool call structure for processing
                        response.tool_calls = [fallback_tool_call]
                        # Clear content to avoid showing raw JSON to user
                        response.content = "I am processing your request..."

                messages.append(response)

                if not response.tool_calls:
                    final_response = response
                    break

                # Execute tools
                graphql_result = None
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    if tool_name in self.tool_map:
                        tool_result = self.tool_map[tool_name].invoke(tool_args)

                        try:
                            graphql_result = json.loads(tool_result)
                        except:
                            graphql_result = None

                        tool_msg = ToolMessage(
                            tool_call_id=tool_call["id"],
                            content=str(tool_result),
                            name=tool_name,
                        )
                        messages.append(tool_msg)

                # Analyze result for formatting (only from the last tool call)
                if graphql_result and (
                    graphql_result.get("data")  # Check if data is not None/Empty
                    or graphql_result.get("type") == "prediction"
                ):
                    try:
                        formatted_data = ResponseFormatter.analyze_and_format(
                            graphql_result, user_query
                        )
                    except Exception as e:
                        print(f"Error formatting data: {e}")
                        # Fallback to text
                        pass

            if not final_response:
                # If loop finished without final response (rare), force one
                final_response = self.llm_with_tools.invoke(messages)
                messages.append(final_response)

            # CLEANUP: Remove raw JSON from final response if leaked
            content = final_response.content

            # 1. Strip JSON blocks
            if (
                "{" in content
                and "}" in content
                and ("name" in content or "parameters" in content)
            ):
                content = re.sub(r'\{.*"name":.*\}', "", content, flags=re.DOTALL)
                content = re.sub(r"```json.*?```", "", content, flags=re.DOTALL)

            # 2. Strip "I apologize" messages if they are just filler
            content = re.sub(
                r"(?i)^(I apologize|I'm sorry|I am sorry).+?(\n|$)",
                "",
                content,
                flags=re.MULTILINE,
            )

            # 3. Strip verbose JSON explanations (The "Mansplaining" fix)
            # Remove lines starting with "This is a JSON" or "Here is the JSON"
            content = re.sub(
                r"(?i)^(This is a JSON|Here is the JSON|The JSON object|The output contains|Based on the JSON).+?(\n|$)",
                "",
                content,
                flags=re.MULTILINE,
            )
            # Remove code blocks that look like JS parsing tutorials
            content = re.sub(
                r"const data = JSON\.parse.*", "", content, flags=re.DOTALL
            )
            # Remove line-by-line field descriptions
            content = re.sub(
                r"^\s*-\s*\*\*\w+\*\*:\s*.*$", "", content, flags=re.MULTILINE
            )

            content = content.strip()
            if not content:
                content = "I found the data for you. Check the visual card below! 📉"

            self.conversation_history[session_id] = messages

            # Save assistant response
            self._save_to_db(session_id, "assistant", content, formatted_data)

            return {
                "answer": content,
                "status": "success",
                "formatted_data": formatted_data,
            }

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "answer": "I apologize, but I encountered an error processing your request.",
                "error": str(e),
                "status": "error",
            }
