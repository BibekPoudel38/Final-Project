// Sample API Responses for All Display Types
// Use these to build and test your React UI components

// ============================================
// 1. METRICS RESPONSE
// ============================================
export const metricsResponse = {
  "answer": "Here's a summary of your inventory metrics.",
  "logs": ["Calling 1 tool(s)", "Query: query { allInventory { edges { node { ... } } } }"],
  "status": "success",
  "formatted_data": {
    "display_type": "metrics",
    "data": {
      "metrics": [
        {
          "label": "Total Items",
          "value": 150,
          "format": "number",
          "icon": "📦"
        },
        {
          "label": "Total Inventory Value",
          "value": 45000.50,
          "format": "currency",
          "icon": "💰"
        },
        {
          "label": "Low Stock Items",
          "value": 12,
          "format": "number",
          "icon": "⚠️",
          "color": "warning"
        },
        {
          "label": "Out of Stock",
          "value": 3,
          "format": "number",
          "icon": "🚫",
          "color": "danger"
        },
        {
          "label": "Average Price",
          "value": 125.75,
          "format": "currency",
          "icon": "📊"
        }
      ]
    },
    "metadata": {
      "title": "Inventory Metrics",
      "layout": "grid"
    }
  }
};

// ============================================
// 2. PIE CHART RESPONSE
// ============================================
export const pieChartResponse = {
  "answer": "Here's the distribution of inventory by type.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "chart",
    "data": {
      "chart_type": "pie",
      "labels": ["Electronics", "Furniture", "Office Supplies", "Tools", "Other"],
      "datasets": [{
        "label": "Items by Type",
        "data": [45, 30, 25, 20, 15],
        "backgroundColor": [
          "#FF6384",
          "#36A2EB",
          "#FFCE56",
          "#4BC0C0",
          "#9966FF"
        ]
      }]
    },
    "metadata": {
      "title": "Inventory Distribution by Type",
      "description": "Showing 135 items across 5 categories"
    }
  }
};

// ============================================
// 3. BAR CHART RESPONSE (Price Comparison)
// ============================================
export const barChartPriceResponse = {
  "answer": "Here are the top 10 items by price.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "chart",
    "data": {
      "chart_type": "bar",
      "labels": [
        "Premium Laptop",
        "Office Desk",
        "Ergonomic Chair",
        "Monitor 27\"",
        "Printer Pro",
        "Tablet Device",
        "Keyboard Mech",
        "Mouse Wireless",
        "Webcam HD",
        "Headset Pro"
      ],
      "datasets": [{
        "label": "Selling Price",
        "data": [1299.99, 899.50, 599.99, 449.00, 399.99, 349.00, 149.99, 79.99, 69.99, 59.99],
        "backgroundColor": "#36A2EB"
      }]
    },
    "metadata": {
      "title": "Top 10 Items by Price",
      "yAxisLabel": "Price ($)"
    }
  }
};

// ============================================
// 4. BAR CHART RESPONSE (Stock Levels)
// ============================================
export const barChartStockResponse = {
  "answer": "Here are the items with lowest stock levels.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "chart",
    "data": {
      "chart_type": "bar",
      "labels": [
        "Widget A",
        "Component B",
        "Part C",
        "Tool D",
        "Supply E",
        "Item F",
        "Product G",
        "Material H"
      ],
      "datasets": [
        {
          "label": "Current Stock",
          "data": [5, 8, 12, 15, 18, 22, 25, 30],
          "backgroundColor": "#FF6384"
        },
        {
          "label": "Min Stock",
          "data": [10, 10, 15, 20, 20, 25, 30, 35],
          "backgroundColor": "#FFCE56"
        }
      ]
    },
    "metadata": {
      "title": "Stock Levels (Lowest 8 Items)",
      "yAxisLabel": "Quantity"
    }
  }
};

// ============================================
// 5. TABLE RESPONSE
// ============================================
export const tableResponse = {
  "answer": "Here's a list of all inventory items.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "table",
    "data": {
      "columns": [
        {
          "key": "id",
          "label": "ID",
          "type": "text",
          "width": "80px"
        },
        {
          "key": "itemName",
          "label": "Item Name",
          "type": "text",
          "width": "200px",
          "sortable": true
        },
        {
          "key": "quantity",
          "label": "Quantity",
          "type": "number",
          "width": "100px",
          "sortable": true
        },
        {
          "key": "quantityUnit",
          "label": "Unit",
          "type": "text",
          "width": "80px"
        },
        {
          "key": "type",
          "label": "Type",
          "type": "text",
          "width": "120px",
          "filterable": true
        },
        {
          "key": "supplier",
          "label": "Supplier",
          "type": "text",
          "width": "150px",
          "filterable": true
        },
        {
          "key": "costPrice",
          "label": "Cost",
          "type": "currency",
          "width": "100px",
          "sortable": true
        },
        {
          "key": "sellingPrice",
          "label": "Price",
          "type": "currency",
          "width": "100px",
          "sortable": true
        },
        {
          "key": "isActive",
          "label": "Active",
          "type": "boolean",
          "width": "80px"
        }
      ],
      "rows": [
        {
          "id": {"value": "1", "formatted": "1"},
          "itemName": {"value": "Premium Laptop", "formatted": "Premium Laptop"},
          "quantity": {"value": 25, "formatted": "25"},
          "quantityUnit": {"value": "units", "formatted": "units"},
          "type": {"value": "Electronics", "formatted": "Electronics"},
          "supplier": {"value": "Tech Corp", "formatted": "Tech Corp"},
          "costPrice": {"value": 899.99, "formatted": "$899.99"},
          "sellingPrice": {"value": 1299.99, "formatted": "$1,299.99"},
          "isActive": {"value": true, "formatted": "✓"}
        },
        {
          "id": {"value": "2", "formatted": "2"},
          "itemName": {"value": "Office Desk", "formatted": "Office Desk"},
          "quantity": {"value": 15, "formatted": "15"},
          "quantityUnit": {"value": "units", "formatted": "units"},
          "type": {"value": "Furniture", "formatted": "Furniture"},
          "supplier": {"value": "Furniture Plus", "formatted": "Furniture Plus"},
          "costPrice": {"value": 599.00, "formatted": "$599.00"},
          "sellingPrice": {"value": 899.50, "formatted": "$899.50"},
          "isActive": {"value": true, "formatted": "✓"}
        },
        {
          "id": {"value": "3", "formatted": "3"},
          "itemName": {"value": "Printer Paper", "formatted": "Printer Paper"},
          "quantity": {"value": 0, "formatted": "0"},
          "quantityUnit": {"value": "boxes", "formatted": "boxes"},
          "type": {"value": "Office Supplies", "formatted": "Office Supplies"},
          "supplier": {"value": "Office Depot", "formatted": "Office Depot"},
          "costPrice": {"value": 15.99, "formatted": "$15.99"},
          "sellingPrice": {"value": 24.99, "formatted": "$24.99"},
          "isActive": {"value": true, "formatted": "✓"}
        }
      ],
      "total_count": 3
    },
    "metadata": {
      "title": "Inventory Items (3 items)",
      "searchable": true,
      "sortable": true,
      "exportable": true,
      "pagination": {
        "enabled": false,
        "page_size": 10
      }
    }
  }
};

// ============================================
// 6. LIST RESPONSE
// ============================================
export const listResponse = {
  "answer": "Here are the items that are out of stock.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "list",
    "data": {
      "items": [
        {
          "id": "3",
          "title": "Printer Paper",
          "subtitle": "0 boxes",
          "details": [
            "Type: Office Supplies",
            "Supplier: Office Depot",
            "Price: $24.99"
          ],
          "status": "out_of_stock",
          "icon": "📦"
        },
        {
          "id": "7",
          "title": "USB Cables",
          "subtitle": "0 units",
          "details": [
            "Type: Electronics",
            "Supplier: Tech Corp",
            "Price: $9.99"
          ],
          "status": "out_of_stock",
          "icon": "📦"
        },
        {
          "id": "12",
          "title": "Stapler",
          "subtitle": "0 units",
          "details": [
            "Type: Office Supplies",
            "Supplier: Office Depot",
            "Price: $12.50"
          ],
          "status": "out_of_stock",
          "icon": "📦"
        }
      ]
    },
    "metadata": {
      "title": "Out of Stock Items (3)",
      "layout": "vertical"
    }
  }
};

// ============================================
// 7. CARD RESPONSE (Single Item)
// ============================================
export const cardResponse = {
  "answer": "Here are the details for Premium Laptop.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "card",
    "data": {
      "title": "Premium Laptop",
      "sections": [
        {
          "title": "Basic Information",
          "fields": [
            {"label": "Item Name", "value": "Premium Laptop"},
            {"label": "Type", "value": "Electronics"},
            {"label": "Description", "value": "High-performance laptop with 16GB RAM and 512GB SSD"}
          ]
        },
        {
          "title": "Stock Information",
          "fields": [
            {"label": "Current Quantity", "value": "25 units"},
            {"label": "Minimum Quantity", "value": "10 units"},
            {"label": "Auto Reorder", "value": "Yes"}
          ]
        },
        {
          "title": "Pricing",
          "fields": [
            {"label": "Cost Price", "value": "$899.99"},
            {"label": "Selling Price", "value": "$1,299.99"},
            {"label": "Margin", "value": "$400.00 (44.4%)"}
          ]
        },
        {
          "title": "Supplier",
          "fields": [
            {"label": "Supplier Name", "value": "Tech Corp"},
            {"label": "Last Restock", "value": "2025-11-15"}
          ]
        }
      ]
    },
    "metadata": {
      "item_id": "1",
      "status": "active"
    }
  }
};

// ============================================
// 8. SUPPLIER TABLE RESPONSE
// ============================================
export const supplierTableResponse = {
  "answer": "Here's a list of all suppliers.",
  "logs": ["Calling 1 tool(s)"],
  "status": "success",
  "formatted_data": {
    "display_type": "table",
    "data": {
      "columns": [
        {"key": "supplierName", "label": "Supplier Name", "type": "text", "sortable": true},
        {"key": "contactPerson", "label": "Contact Person", "type": "text"},
        {"key": "supplierEmail", "label": "Email", "type": "email"},
        {"key": "supplierPhone", "label": "Phone", "type": "phone"}
      ],
      "rows": [
        {
          "supplierName": {"value": "Tech Corp", "formatted": "Tech Corp"},
          "contactPerson": {"value": "John Smith", "formatted": "John Smith"},
          "supplierEmail": {"value": "john@techcorp.com", "formatted": "john@techcorp.com"},
          "supplierPhone": {"value": "+1-555-0100", "formatted": "+1-555-0100"}
        },
        {
          "supplierName": {"value": "Furniture Plus", "formatted": "Furniture Plus"},
          "contactPerson": {"value": "Jane Doe", "formatted": "Jane Doe"},
          "supplierEmail": {"value": "jane@furnitureplus.com", "formatted": "jane@furnitureplus.com"},
          "supplierPhone": {"value": "+1-555-0200", "formatted": "+1-555-0200"}
        },
        {
          "supplierName": {"value": "Office Depot", "formatted": "Office Depot"},
          "contactPerson": {"value": "Bob Johnson", "formatted": "Bob Johnson"},
          "supplierEmail": {"value": "bob@officedepot.com", "formatted": "bob@officedepot.com"},
          "supplierPhone": {"value": "+1-555-0300", "formatted": "+1-555-0300"}
        }
      ],
      "total_count": 3
    },
    "metadata": {
      "title": "Suppliers (3)",
      "searchable": true,
      "exportable": true
    }
  }
};

// ============================================
// 9. TEXT-ONLY RESPONSE (Fallback)
// ============================================
export const textResponse = {
  "answer": "I can help you with inventory and supplier queries. Try asking about stock levels, prices, or supplier information.",
  "logs": [],
  "status": "success"
};

// ============================================
// 10. ERROR RESPONSE
// ============================================
export const errorResponse = {
  "answer": "An error occurred while processing your request.",
  "error": "GraphQL query failed: Cannot query field 'invalidField'",
  "status": "error"
};
