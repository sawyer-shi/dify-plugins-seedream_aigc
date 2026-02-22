# Seedream AIGC

A powerful Dify plugin providing comprehensive AI-powered image and video generation capabilities using Volcengine Doubao's latest Seedream and Seedance models. Supports text-to-image, text-to-video, image-to-image, image-to-video, multi-image fusion, and more with professional-grade quality and flexible configuration options.

## Version Information

- **Current Version**: v0.0.1
- **Release Date**: 2026-02-13
- **Compatibility**: Dify Plugin Framework
- **Python Version**: 3.12

### Version History
- **v0.0.1** (2026-02-13): Initial release with image and video generation capabilities

## Quick Start

1. Install the plugin in your Dify environment
2. Configure your Volcengine API credentials (API Key)
3. Start generating images and videos with AI

## Key Features
<img width="728" height="1412" alt="CN" src="https://github.com/user-attachments/assets/33b43f72-9960-4044-8f0b-efafc1fc7fbb"/><img width="732" height="1610" alt="EN" src="https://github.com/user-attachments/assets/6ced5493-dc55-4f35-9a47-bd23d93db18b"/>

- **Multiple Generation Modes**: Text-to-image, text-to-video, image-to-image, image-to-video, multi-image fusion
- **Latest AI Models**: Supports Seedream 4.0, 4.5, 5.0 Lite for images; Seedance 1.0 Pro, 1.0 Pro Fast, 1.5 Pro, 2.0 for videos
- **Flexible Image Sizes**: Multiple aspect ratios from 1:1 to 21:9 with resolutions up to 3024x1296
- **Video Generation**: Create videos up to 12 seconds with synchronized audio (Seedance 1.5 Pro)
- **Multi-Image Support**: Generate images from multiple reference images (2-14 images)
- **First-Last Frame Video**: Create videos from first and last frame images
- **Batch Generation**: Generate multiple images in a single request
- **Draft Mode**: Quick preview generation for faster iteration
- **Watermark Control**: Optional AI-generated watermark for content authenticity

## Core Features

### Image Generation

#### Text to Image (text_2_image)
Generate images from text descriptions using Seedream models.
- **Supported Models**: Seedream 4.0, Seedream 4.5, Seedream 5.0 Lite
- **Features**:
  - Multiple aspect ratios (1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3, 21:9)
  - High resolution up to 3024x1296
  - Optional watermark
  - Fast generation speed

#### Image to Image (image_2_image)
Generate images from text and a reference image.
- **Supported Models**: Seedream 4.0, Seedream 4.5, Seedream 5.0 Lite
- **Features**:
  - Reference image guided generation
  - Multiple aspect ratios
  - Optional watermark
  - Support for jpeg, png, webp, bmp, tiff, gif formats (max 10MB)

#### Multi-Image Fusion (multi_images_2_image)
Generate an image from text and multiple reference images (2-14 images).
- **Supported Models**: Seedream 4.0, Seedream 4.5, Seedream 5.0 Lite
- **Features**:
  - Combine up to 14 reference images
  - Intelligent image fusion
  - Multiple aspect ratios
  - Optional watermark

#### Multi-Image Group (multi_images_2_multi_images)
Generate a group of images from text and multiple reference images.
- **Supported Models**: Seedream 4.0, Seedream 4.5, Seedream 5.0 Lite
- **Features**:
  - Generate 1-15 images per request
  - Multiple reference images support (2-14)
  - Batch generation
  - Multiple aspect ratios

### Video Generation

#### Text to Video (text_2_video)
Generate videos from text descriptions using Seedance models.
- **Supported Models**: Seedance 1.0 Pro, Seedance 1.0 Pro Fast, Seedance 1.5 Pro, Seedance 2.0
- **Features**:
  - Duration: 2-12 seconds
  - Resolution: 480p, 720p, 1080p
  - Aspect ratios: 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive
  - Synchronized audio generation (Seedance 1.5 Pro)
  - Draft mode for quick preview
  - Fixed camera option
  - Service tier selection (default/flex)

#### Image to Video (image_2_video)
Generate video from a single image with text description.
- **Supported Models**: Seedance 1.0 Pro, Seedance 1.0 Pro Fast, Seedance 1.5 Pro, Seedance 2.0
- **Features**:
  - Single image input
  - Duration: 2-12 seconds
  - Resolution: 480p, 720p, 1080p
  - Adaptive aspect ratio support
  - Synchronized audio generation
  - Draft mode available

#### First-Last Frame Video (images_2_video)
Generate video from first and last frame images.
- **Supported Models**: Seedance 1.0 Pro, Seedance 1.5 Pro, Seedance 2.0
- **Features**:
  - First and last frame input
  - Smooth transition generation
  - Duration: 2-12 seconds
  - Resolution: 480p, 720p, 1080p
  - Synchronized audio generation
  - Draft mode available

#### Video Query (video_query)
Query the status and results of video generation tasks.
- **Features**:
  - Real-time task status
  - Video download URL retrieval
  - Last frame image return option

## Technical Advantages

- **Latest AI Models**: Access to Doubao's newest Seedream and Seedance models
- **High Quality Output**: Professional-grade image and video generation
- **Flexible Configuration**: Extensive parameter options for fine-tuning
- **Async Processing**: Efficient video generation with task-based workflow
- **Multi-Format Support**: Support for various image and video formats
- **Audio Generation**: Automatic synchronized audio for videos
- **Batch Processing**: Generate multiple images efficiently
- **Draft Mode**: Quick preview for faster iteration cycles

## Requirements

- Python 3.12
- Dify Platform access
- Volcengine API credentials (API Key)
- Required Python packages (installed via requirements.txt):
  - dify_plugin>=0.2.0
  - requests>=2.31.0,<3.0.0
  - pillow>=10.0.0,<11.0.0

## Installation & Configuration

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your Volcengine API credentials in the plugin settings:
   - **API Key**: Your Volcengine API key

3. Install the plugin in your Dify environment

## Usage

### Image Generation Tools

#### 1. Text to Image
Generate images from text descriptions.
- **Parameters**:
  - `prompt`: Text description of the image (required)
  - `size`: Image size (default: 2048x2048)
  - `watermark`: Enable/disable watermark (default: true)
  - `model`: Model version (default: Seedream 4.5)

#### 2. Image to Image
Generate images from text and a reference image.
- **Parameters**:
  - `prompt`: Text description (required)
  - `input_image_file`: Reference image file (required)
  - `size`: Image size (default: 2048x2048)
  - `watermark`: Enable/disable watermark (default: true)
  - `model`: Model version (default: Seedream 4.5)

#### 3. Multi-Image Fusion
Generate an image from multiple reference images.
- **Parameters**:
  - `prompt`: Text description (required)
  - `input_image_files`: Reference images (2-14 images, required)
  - `size`: Image size (default: 2048x2048)
  - `watermark`: Enable/disable watermark (default: true)
  - `model`: Model version (default: Seedream 4.5)

#### 4. Multi-Image Group
Generate multiple images from reference images.
- **Parameters**:
  - `prompt`: Text description (required)
  - `input_image_files`: Reference images (2-14 images, required)
  - `max_images`: Maximum images to generate (1-15, default: 3)
  - `size`: Image size (default: 2048x2048)
  - `watermark`: Enable/disable watermark (default: true)
  - `model`: Model version (default: Seedream 4.5)

### Video Generation Tools

#### 5. Text to Video
Generate videos from text descriptions.
- **Parameters**:
  - `prompt`: Text description (max 500 chars, required)
  - `model`: Model version (default: Seedance 1.5 Pro)
  - `resolution`: Video resolution (default: 720p)
  - `ratio`: Aspect ratio (default: 16:9)
  - `duration`: Duration in seconds (2-12, default: 5)
  - `seed`: Random seed (-1 for random)
  - `camera_fixed`: Fixed camera position
  - `watermark`: Enable/disable watermark
  - `generate_audio`: Generate synchronized audio
  - `draft`: Draft mode for quick preview
  - `return_last_frame`: Return last frame image in query
  - `service_tier`: Service tier (default/flex)

#### 6. Image to Video
Generate video from a single image.
- **Parameters**:
  - `prompt`: Text description (required)
  - `input_image_file`: Input image (required)
  - Other parameters same as Text to Video

#### 7. First-Last Frame Video
Generate video from first and last frame images.
- **Parameters**:
  - `prompt`: Text description (required)
  - `first_frame_file`: First frame image (required)
  - `last_frame_file`: Last frame image (required)
  - Other parameters same as Text to Video

#### 8. Video Query
Query video generation task status.
- **Parameters**:
  - `task_id`: Video generation task ID (required)
  - `download_video`: Download video file when available (default: true)

## Supported Image Sizes

| Aspect Ratio | Resolution |
|-------------|------------|
| 1:1 | 2048x2048 |
| 4:3 | 2304x1728 |
| 3:4 | 1728x2304 |
| 16:9 | 2560x1440 |
| 9:16 | 1440x2560 |
| 3:2 | 2496x1664 |
| 2:3 | 1664x2496 |
| 21:9 | 3024x1296 |

## Notes

- Video generation is asynchronous; use Video Query to check status and retrieve results
- Seedance 1.5 Pro supports synchronized audio generation
- Draft mode provides faster generation for quick previews
- Flex service tier offers cost-effective processing with longer wait times
- Maximum prompt length for video generation is 500 characters
- Reference images should be under 10MB in size
- Multi-image fusion supports 2-14 reference images

## Developer Information

- **Author**: `https://github.com/sawyer-shi`
- **Email**: sawyer36@foxmail.com
- **License**: Apache License 2.0
- **Source Code**: `https://github.com/sawyer-shi/dify-plugins-seedream_aigc`
- **Support**: Through Dify platform and GitHub Issues

## License Notice

This project is licensed under Apache License 2.0. See [LICENSE](LICENSE) file for full license text.

---

**Ready to create stunning images and videos with AI?**
