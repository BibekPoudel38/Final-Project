import os
import json
import time
import mimetypes
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import MediaGeneration
from google import genai
from google.genai import types


class MediaGenerationView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

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

    def generate_image(self, client, prompt, input_image=None):
        model = "gemini-2.0-flash-image"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        # Add input image if provided
        # Note: For now, we are just using text prompt as the primary driver.
        # If input_image is needed for image-to-image, it would be added here.
        # But the user request implies using the uploaded asset.
        # Let's check if we can add the image bytes.
        if input_image:
            # Read image data
            image_data = input_image.read()
            contents[0].parts.append(
                types.Part.from_bytes(
                    data=image_data, mime_type=input_image.content_type
                )
            )

        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            # image_config=types.ImageConfig(image_size="1024x1024"),  # Adjust as needed
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            part = response.candidates[0].content.parts[0]
            if part.inline_data:
                return part.inline_data.data, part.inline_data.mime_type
        return None, None

    def generate_video(self, client, prompt):
        model = "veo-2.0-generate-001"
        video_config = types.GenerateVideosConfig(
            aspect_ratio="16:9",  # Default, can be adjusted based on input
            number_of_videos=1,
            duration_seconds=8,
            person_generation="ALLOW_ALL",
        )

        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=video_config,
        )

        # Wait for operation
        while not operation.done:
            time.sleep(5)  # Poll every 5 seconds
            operation = client.operations.get(operation)

        result = operation.result
        if result and result.generated_videos:
            video = result.generated_videos[0].video
            # Download video content
            # The client.files.download method saves to a file, but we want bytes.
            # We might need to save it temporarily or see if we can get bytes.
            # The provided code uses client.files.download(file=video) which downloads to cwd?
            # Actually, let's look at the provided code: client.files.download(file=generated_video.video)
            # It seems it downloads to a file.
            # We can use `client.files.content(file_name=video.name)` if available, or just download to temp.

            # Let's try to get the content directly if possible.
            # If not, we download to a temp file and read it.
            # For now, let's assume we can download it.
            # Actually, the python client `download` method might write to a file.
            # Let's use a temp file.
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                client.files.download(
                    file=video, config=types.DownloadFileConfig(destination=tmp.name)
                )
                tmp.seek(0)
                data = tmp.read()
                os.unlink(tmp.name)  # Delete temp file
                return data, "video/mp4"
        return None, None

    def post(self, request, *args, **kwargs):
        data_str = request.data.get("data")
        if not data_str:
            return Response({"error": "No data provided"}, status=400)

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=400)

        input_image = request.FILES.get("media_file")
        mode = data.get("mode", "image")
        prompt = self.construct_prompt(data)

        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        generated_data = None
        mime_type = None

        try:
            if mode == "video":
                generated_data, mime_type = self.generate_video(client, prompt)
            else:
                generated_data, mime_type = self.generate_image(
                    client, prompt, input_image
                )
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        if not generated_data:
            return Response({"error": "Generation failed"}, status=500)

        # Save to model
        media_gen = MediaGeneration(
            user=request.user,
            prompt=prompt,
            original_data=data,
            input_image=input_image,
            media_type=mode,
            is_public=False,  # Default
        )

        # Save generated file
        ext = mimetypes.guess_extension(mime_type) or ".bin"
        filename = f"generated_{int(time.time())}{ext}"
        media_gen.generated_file.save(filename, ContentFile(generated_data))
        media_gen.save()

        return Response(
            {
                "id": media_gen.id,
                "media_url": media_gen.generated_file.url,
                "prompt": prompt,
            }
        )
