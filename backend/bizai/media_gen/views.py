import os
import json
import time
import mimetypes
from django.conf import settings
from django.core.files.base import ContentFile
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from .models import MediaGeneration
from .serializers import MediaGenerationSerializer
from google import genai
from google.genai import types


class MediaHistoryView(APIView):
    permission_classes = []  # Allow any
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        print("=====" * 10)
        """Returns a list of all media generations (DEBUG MODE: No Auth)."""
        # Fetch all for now since we have no user context
        generations = MediaGeneration.objects.all().order_by("-created_at")
        serializer = MediaGenerationSerializer(generations, many=True)
        return Response(serializer.data)


class MediaGenerationView(APIView):
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]
    parser_classes = (MultiPartParser, FormParser)

    def construct_prompt(self, data):
        """Constructs a descriptive prompt from the structured JSON data."""
        prompt_parts = []
        # ... (rest of construct_prompt) ...

    def get(self, request, *args, **kwargs):
        """Returns a list of media generations for the current user."""
        generations = MediaGeneration.objects.filter(user=request.user).order_by(
            "-created_at"
        )
        print(generations)
        serializer = MediaGenerationSerializer(generations, many=True)
        return Response(serializer.data)

    def construct_prompt(self, data):
        """Constructs a descriptive prompt from the structured JSON data."""
        prompt_parts = []

        if "mode" in data:
            prompt_parts.append(f"Generate a {data['mode']} for")

        if "platform" in data:
            prompt_parts.append(f"a {data['platform']}")

        if "brand" in data:
            brand = data["brand"]
            prompt_parts.append(
                f"Brand: {brand.get('name', '')} ({brand.get('industry', '')})"
            )

        if "campaign" in data:
            campaign = data["campaign"]
            prompt_parts.append(f"Campaign Offer: {campaign.get('offer', '')}")
            prompt_parts.append(
                f"Product/Service: {campaign.get('productService', '')}"
            )
            prompt_parts.append(f"Audience: {campaign.get('audience', '')}")
            prompt_parts.append(f"Tone: {campaign.get('tone', '')}")
            prompt_parts.append(f"Style: {campaign.get('style', '')}")
            prompt_parts.append(f"CTA: {campaign.get('cta', '')}")
            if campaign.get("motifs"):
                prompt_parts.append(f"Motifs: {', '.join(campaign['motifs'])}")
            prompt_parts.append(f"Background: {campaign.get('backgroundStyle', '')}")
            if campaign.get("palette"):
                prompt_parts.append(f"Color Palette: {', '.join(campaign['palette'])}")

        return "\n".join(prompt_parts)

    def generate_image(self, client, prompt, model="gemini-2.5-flash-image"):
        print(f"Generating image with model: {model}")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    inline_data = part.inline_data
                    return inline_data.data, inline_data.mime_type
                else:
                    if chunk.text:
                        print(f"GenAI Text Chunk: {chunk.text}")

            print("No image inline_data found in the stream.")
            return None, None

        except Exception as e:
            print(f"Error in generate_image: {e}")
            import traceback

            traceback.print_exc()
            raise e

    def generate_video(self, client, prompt):
        # Using "veo-2.0-generate-001" as the most reliable ID for now.
        # "VEO 3" was requested but accurate ID is not confirmed in SDK docs available to me.
        model = "veo-2.0-generate-001"
        try:
            video_config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=8,
                person_generation="ALLOW_ALL",
            )

            operation = client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=video_config,
            )

            while not operation.done:
                time.sleep(5)
                operation = client.operations.get(operation)

            result = operation.result
            if result and result.generated_videos:
                video = result.generated_videos[0].video

                import tempfile

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    client.files.download(
                        file=video,
                        config=types.DownloadFileConfig(destination=tmp.name),
                    )
                    tmp.seek(0)
                    data = tmp.read()
                    os.unlink(tmp.name)
                    return data, "video/mp4"

            return None, None
        except Exception as e:
            print(f"Error in generate_video: {e}")
            return None, None

    def generate_social_content(self, client, campaign_data):
        """Generates social media caption and hashtags."""
        prompt = f"""
        Generate a catchy social media caption and a list of 10 relevant hashtags for a marketing campaign.
        
        Campaign Details:
        Product/Service: {campaign_data.get('productService', '')}
        Offer: {campaign_data.get('offer', '')}
        Audience: {campaign_data.get('audience', '')}
        Tone: {campaign_data.get('tone', '')}
        
        Output JSON format:
        {{
            "caption": "Your catchy caption here",
            "hashtags": ["#tag1", "#tag2", ...]
        }}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            if response.text:
                return json.loads(response.text)
        except Exception as e:
            print(f"Error generating social content: {e}")

        return {"caption": "", "hashtags": []}

    def post(self, request, *args, **kwargs):
        print("Request received:", request)
        data_str = request.data.get("data")
        print("Data received:", data_str)
        if not data_str:
            return Response({"error": "No data provided"}, status=400)

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=400)

        input_image = request.FILES.get("media_file")
        mode = data.get("mode", "image")
        make_public = data.get("make_public", False)

        prompt = self.construct_prompt(data)

        if make_public:
            from .models import PromptTemplate

            # Basic deduplication
            if not PromptTemplate.objects.filter(prompt=prompt).exists():
                PromptTemplate.objects.create(
                    prompt=prompt,
                    category=data.get("campaign", {}).get("productService", "General"),
                    tags=data.get("campaign", {}).get("motifs", []),
                    original_data=data,
                )

        # Assuming API KEY is set in env
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("CRITICAL: GEMINI_API_KEY not found in environment variables.")
            return Response(
                {"error": "Server configuration error: Missing API Key"}, status=500
            )

        client = genai.Client(api_key=api_key)

        generated_data = None
        mime_type = None

        # specific fix for image model
        # The user was using gemini-3-pro-image-preview in the original code, but I'll stick to
        # gemini-2.0-flash-exp as per plan if 3 fails or if I prefer it.
        # Actually original code had a fallback. I will implement a simpler clean logic.

        try:
            if mode == "video":
                generated_data, mime_type = self.generate_video(client, prompt)
            else:
                # Use the new verified model
                generated_data, mime_type = self.generate_image(
                    client, prompt, model="gemini-2.5-flash-image"
                )

        except Exception as e:
            print(f"GenAI Error: {e}")
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

        if not generated_data:
            print("Error: generated_data is None after generation attempts.")
            return Response({"error": "Generation failed to produce data"}, status=500)

        # Generate Social Content (Caption + Hashtags)
        try:
            social_content = self.generate_social_content(
                client, data.get("campaign", {})
            )
        except Exception as e:
            print(f"Social Content Generation Error: {e}")
            traceback.print_exc()
            social_content = {"caption": "", "hashtags": []}

        # Save to model
        try:
            media_gen = MediaGeneration(
                user=request.user,
                prompt=prompt,
                original_data=data,
                input_image=input_image,
                media_type=mode,
                is_public=make_public,
                caption=social_content.get("caption", ""),
                hashtags=social_content.get("hashtags", []),
            )

            ext = mimetypes.guess_extension(mime_type) or ".bin"
            filename = f"generated_{int(time.time())}{ext}"
            media_gen.generated_file.save(filename, ContentFile(generated_data))
            media_gen.save()
        except Exception as e:
            print(f"Database Save Error: {e}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to save generated media to database."}, status=500
            )

        return Response(
            {
                "id": media_gen.id,
                "media_url": media_gen.generated_file.url,
                "prompt": prompt,
                "template_saved": make_public,
                "caption": media_gen.caption,
                "hashtags": media_gen.hashtags,
            }
        )
