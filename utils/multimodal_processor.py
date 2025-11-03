import os
import logging
from typing import Optional, Dict, Any, Tuple
import tempfile
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultimodalProcessor:
    """Processor for audio and video files to extract text using speech-to-text"""

    def __init__(self):
        self.supported_audio_formats = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import whisper
            self.whisper_available = True
            logger.info("OpenAI Whisper available for speech-to-text")
        except ImportError:
            self.whisper_available = False
            logger.warning("OpenAI Whisper not available - speech-to-text disabled")

        try:
            # Try new import path first (moviepy 2.x)
            try:
                import moviepy
                self.moviepy_available = True
                logger.info("MoviePy available for video processing")
            except ImportError:
                # Fallback to old import path (moviepy 1.x)
                import moviepy.editor as mp
                self.moviepy_available = True
                logger.info("MoviePy available for video processing")
        except ImportError:
            self.moviepy_available = False
            logger.warning("MoviePy not available - video processing disabled")

    def is_supported_file(self, filename: str) -> bool:
        """Check if the file format is supported"""
        if not filename:
            return False

        _, ext = os.path.splitext(filename.lower())
        return ext in self.supported_audio_formats or ext in self.supported_video_formats

    def is_audio_file(self, filename: str) -> bool:
        """Check if file is an audio file"""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.supported_audio_formats

    def is_video_file(self, filename: str) -> bool:
        """Check if file is a video file"""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.supported_video_formats

    def extract_text_from_audio_video(self, file_path: str, model_size: str = "base") -> str:
        """
        Extract text from audio/video file using Whisper

        Args:
            file_path: Path to the audio/video file
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

        Returns:
            Extracted text content
        """
        if not self.whisper_available:
            raise Exception("OpenAI Whisper not installed. Please install with: pip install openai-whisper")

        try:
            import whisper
            
            # Configure FFmpeg path for Whisper
            # Whisper uses ffmpeg-python which looks for ffmpeg in PATH
            # Use imageio-ffmpeg's bundled ffmpeg if system ffmpeg not available
            try:
                import imageio_ffmpeg
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                # Add ffmpeg directory to PATH temporarily
                ffmpeg_dir = os.path.dirname(ffmpeg_path)
                old_path = os.environ.get('PATH', '')
                os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{old_path}"
                logger.info(f"Using FFmpeg from: {ffmpeg_path}")
            except Exception as e:
                logger.warning(f"Could not configure imageio-ffmpeg: {e}")
                # Continue anyway, maybe system ffmpeg is available

            logger.info(f"Loading Whisper model: {model_size}")
            model = whisper.load_model(model_size)

            logger.info(f"Transcribing file: {file_path}")
            result = model.transcribe(file_path, language='en')

            text = result["text"].strip()
            if not text:
                raise Exception("No speech detected in the audio/video file")

            logger.info(f"Successfully extracted {len(text)} characters of text")
            return text

        except Exception as e:
            logger.error(f"Error during speech-to-text: {e}")
            raise Exception(f"Speech-to-text failed: {str(e)}")

    def extract_audio_from_video(self, video_path: str, audio_path: str) -> bool:
        """
        Extract audio track from video file

        Args:
            video_path: Path to video file
            audio_path: Path where to save extracted audio

        Returns:
            True if successful, False otherwise
        """
        if not self.moviepy_available:
            # Try using ffmpeg directly
            try:
                cmd = [
                    'ffmpeg', '-i', video_path, '-vn', '-acodec', 'libmp3lame',
                    '-ab', '128k', audio_path, '-y'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"Audio extracted using ffmpeg: {audio_path}")
                    return True
                else:
                    logger.error(f"FFmpeg extraction failed: {result.stderr}")
                    return False

            except FileNotFoundError:
                logger.error("Neither MoviePy nor FFmpeg available for video processing")
                return False
            except Exception as e:
                logger.error(f"Error extracting audio with ffmpeg: {e}")
                return False

        try:
            import moviepy

            logger.info(f"Extracting audio from video: {video_path}")
            video = moviepy.VideoFileClip(video_path)
            
            # Check if video has audio
            if video.audio is None:
                logger.error("Video file has no audio track")
                video.close()
                return False
            
            # MoviePy 2.x API - removed verbose and logger parameters
            try:
                video.audio.write_audiofile(audio_path)
            except TypeError:
                # Fallback for older MoviePy versions
                video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            
            video.close()

            logger.info(f"Audio extracted successfully: {audio_path}")
            return True

        except Exception as e:
            logger.error(f"Error extracting audio with MoviePy: {e}")
            return False

    def extract_captions_from_video(self, video_path: str) -> Optional[str]:
        """
        Extract embedded captions/subtitles from video file using multiple methods
        
        Args:
            video_path: Path to video file
            
        Returns:
            Extracted caption text or None if no captions found
        """
        logger.info(f"Starting caption extraction for: {os.path.basename(video_path)}")
        
        try:
            # Method 1: Try using ffmpeg to extract embedded subtitles
            logger.info("Method 1: Checking for embedded subtitle tracks...")
            caption_text = self._extract_embedded_subtitles(video_path)
            if caption_text:
                logger.info("✓ Successfully extracted embedded subtitles")
                return caption_text
            
            # Method 2: Check for companion subtitle files
            logger.info("Method 2: Checking for companion subtitle files...")
            caption_text = self._check_companion_subtitle_files(video_path)
            if caption_text:
                logger.info("✓ Successfully extracted companion subtitle file")
                return caption_text
            
            # Method 3: Try to extract text from video metadata
            logger.info("Method 3: Checking video metadata for descriptions...")
            caption_text = self._extract_metadata_text(video_path)
            if caption_text:
                logger.info("✓ Successfully extracted metadata text")
                return caption_text
            
            logger.info("✗ No captions found using any extraction method")
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract captions: {e}")
            return None

    def _extract_embedded_subtitles(self, video_path: str) -> Optional[str]:
        """Extract embedded subtitle tracks from video"""
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            # First, get detailed information about the video
            probe_cmd = [
                ffmpeg_path, '-i', video_path, '-hide_banner'
            ]
            
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            # Log video information for debugging
            logger.info("Video file analysis:")
            video_info_lines = []
            subtitle_streams = []
            
            for line in probe_result.stderr.split('\n'):
                line = line.strip()
                if 'Stream #' in line:
                    video_info_lines.append(f"  {line}")
                    if 'subtitle' in line.lower():
                        # Extract stream index
                        try:
                            stream_part = line.split('Stream #')[1].split(':')[1].split('(')[0]
                            subtitle_streams.append(int(stream_part))
                        except:
                            # Fallback parsing
                            if 'subtitle' in line.lower():
                                subtitle_streams.append(len(subtitle_streams))
            
            if video_info_lines:
                logger.info("Streams found:")
                for line in video_info_lines:
                    logger.info(line)
            
            logger.info(f"Detected {len(subtitle_streams)} subtitle streams: {subtitle_streams}")
            
            if not subtitle_streams:
                logger.info("No embedded subtitle streams found in video")
                return None
            
            # Try to extract each subtitle stream
            for i in subtitle_streams:
                try:
                    subtitle_path = f"{video_path}_subtitles_{i}.srt"
                    
                    # Extract subtitles using ffmpeg
                    cmd = [
                        ffmpeg_path, '-i', video_path, '-map', f'0:s:{i}',
                        '-c:s', 'srt', subtitle_path, '-y'
                    ]
                    
                    logger.info(f"Attempting to extract subtitle stream {i}...")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists(subtitle_path):
                        # Check file size
                        file_size = os.path.getsize(subtitle_path)
                        logger.info(f"Extracted subtitle file size: {file_size} bytes")
                        
                        if file_size > 0:
                            # Read and parse SRT file
                            with open(subtitle_path, 'r', encoding='utf-8', errors='ignore') as f:
                                srt_content = f.read()
                            
                            # Clean up subtitle file
                            os.unlink(subtitle_path)
                            
                            # Parse SRT format - extract just the text
                            caption_text = self._parse_srt_content(srt_content)
                            
                            if caption_text and len(caption_text) > 50:
                                logger.info(f"✓ Successfully extracted {len(caption_text)} characters from embedded subtitles (stream {i})")
                                return caption_text
                            else:
                                logger.info(f"Subtitle stream {i} extracted but content too short: {len(caption_text) if caption_text else 0} characters")
                        else:
                            logger.info(f"Subtitle stream {i} extracted but file is empty")
                    else:
                        logger.info(f"Failed to extract subtitle stream {i}: {result.stderr}")
                
                except Exception as e:
                    logger.warning(f"Failed to extract subtitle stream {i}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract embedded subtitles: {e}")
            return None

    def _check_companion_subtitle_files(self, video_path: str) -> Optional[str]:
        """Check for subtitle files with the same name as the video"""
        try:
            base_path = os.path.splitext(video_path)[0]
            subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa', '.sub', '.sbv']
            language_codes = ['', '.en', '.eng', '.english', '.es', '.fr', '.de', '.it', '.pt', '.ru', '.ja', '.ko', '.zh']
            
            logger.info(f"Checking for companion subtitle files for: {os.path.basename(video_path)}")
            
            # Check for exact matches first
            for ext in subtitle_extensions:
                subtitle_file = base_path + ext
                if os.path.exists(subtitle_file):
                    logger.info(f"Found exact match subtitle file: {subtitle_file}")
                    caption_text = self._process_subtitle_file(subtitle_file, ext)
                    if caption_text:
                        return caption_text
            
            # Check for language-specific subtitle files (e.g., video.en.vtt)
            for lang in language_codes:
                if not lang:  # Skip empty string as we already checked exact matches
                    continue
                for ext in subtitle_extensions:
                    subtitle_file = base_path + lang + ext
                    if os.path.exists(subtitle_file):
                        logger.info(f"Found language-specific subtitle file: {subtitle_file}")
                        caption_text = self._process_subtitle_file(subtitle_file, ext)
                        if caption_text:
                            return caption_text
            
            # Check for files in the same directory with similar names (for downloaded videos)
            directory = os.path.dirname(video_path)
            video_basename = os.path.basename(base_path)
            
            try:
                for filename in os.listdir(directory):
                    if filename.startswith(video_basename):
                        for ext in subtitle_extensions:
                            if filename.endswith(ext):
                                subtitle_file = os.path.join(directory, filename)
                                logger.info(f"Found similar-named subtitle file: {subtitle_file}")
                                caption_text = self._process_subtitle_file(subtitle_file, ext)
                                if caption_text:
                                    return caption_text
            except Exception as e:
                logger.warning(f"Could not scan directory for subtitle files: {e}")
            
            logger.info("No companion subtitle files found")
            return None
            
        except Exception as e:
            logger.warning(f"Could not check companion subtitle files: {e}")
            return None

    def _process_subtitle_file(self, subtitle_file: str, ext: str) -> Optional[str]:
        """Process a subtitle file and extract text content"""
        try:
            with open(subtitle_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if ext == '.srt':
                caption_text = self._parse_srt_content(content)
            elif ext == '.vtt':
                caption_text = self._parse_vtt_content(content)
            else:
                # For other formats, try basic text extraction
                caption_text = self._extract_text_from_subtitle_content(content)
            
            if caption_text and len(caption_text) > 50:
                logger.info(f"✓ Extracted {len(caption_text)} characters from {os.path.basename(subtitle_file)}")
                return caption_text
            else:
                logger.info(f"Subtitle file {os.path.basename(subtitle_file)} has insufficient content: {len(caption_text) if caption_text else 0} characters")
                return None
                
        except Exception as e:
            logger.warning(f"Could not process subtitle file {subtitle_file}: {e}")
            return None

    def _extract_metadata_text(self, video_path: str) -> Optional[str]:
        """Try to extract text from video metadata or description"""
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Extract metadata
            cmd = [
                ffmpeg_path, '-i', video_path, '-f', 'ffmetadata', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                metadata_text = result.stdout
                
                # Look for description or comment fields that might contain transcript
                description_text = ""
                for line in metadata_text.split('\n'):
                    if line.startswith('description=') or line.startswith('comment='):
                        desc = line.split('=', 1)[1]
                        if len(desc) > 100:  # Only consider substantial descriptions
                            description_text += desc + " "
                
                if description_text and len(description_text) > 100:
                    logger.info(f"Extracted {len(description_text)} characters from video metadata")
                    return description_text.strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract metadata text: {e}")
            return None

    def _parse_srt_content(self, srt_content: str) -> str:
        """Parse SRT subtitle format and extract text"""
        lines = srt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, numbers, and timestamps
            if line and not line.isdigit() and '-->' not in line:
                # Remove HTML tags if present
                import re
                line = re.sub(r'<[^>]+>', '', line)
                text_lines.append(line)
        
        return ' '.join(text_lines)

    def _parse_vtt_content(self, vtt_content: str) -> str:
        """Parse WebVTT subtitle format and extract text"""
        lines = vtt_content.split('\n')
        text_lines = []
        
        skip_next = False
        for line in lines:
            line = line.strip()
            
            # Skip WebVTT header
            if line.startswith('WEBVTT'):
                continue
            
            # Skip timestamps
            if '-->' in line:
                skip_next = False
                continue
            
            # Skip cue identifiers
            if line and not skip_next and not line.isdigit():
                # Remove HTML tags if present
                import re
                line = re.sub(r'<[^>]+>', '', line)
                if line:
                    text_lines.append(line)
        
        return ' '.join(text_lines)

    def _extract_text_from_subtitle_content(self, content: str) -> str:
        """Basic text extraction from subtitle content"""
        import re
        
        # Remove timestamps (various formats)
        content = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', content)
        content = re.sub(r'\d{2}:\d{2}:\d{2}\s*-->\s*\d{2}:\d{2}:\d{2}', '', content)
        
        # Remove HTML/XML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove subtitle numbers
        content = re.sub(r'^\d+$', '', content, flags=re.MULTILINE)
        
        # Clean up whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        return ' '.join(lines)

    def process_file_from_path(self, file_path: str, filename: str, model_size: str = "base") -> Tuple[str, Dict[str, Any]]:
        """
        Process audio/video file from a file path and extract text

        Args:
            file_path: Path to the audio/video file
            filename: Original filename
            model_size: Whisper model size

        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not self.is_supported_file(filename):
            raise Exception(f"Unsupported file format. Supported formats: {self.supported_audio_formats | self.supported_video_formats}")

        try:
            text = None
            extraction_method = "unknown"
            
            # If it's a video file, try captions first
            if self.is_video_file(filename):
                logger.info("Attempting to extract captions from video...")
                caption_text = self.extract_captions_from_video(file_path)
                
                if caption_text and len(caption_text) > 50:  # Lowered threshold
                    # Successfully extracted captions
                    text = caption_text
                    extraction_method = "captions"
                    logger.info(f"Using extracted captions as text source ({len(caption_text)} characters)")
                else:
                    logger.info("No captions found or captions too short")
                    
                    # Provide more detailed error message
                    error_msg = (
                        "No captions/subtitles found in this video.\n\n"
                        "This app extracts text from:\n"
                        "• Embedded subtitle tracks in video files\n"
                        "• Companion subtitle files (.srt, .vtt, .ass, etc.)\n"
                        "• Video metadata descriptions\n\n"
                        "To use this feature:\n"
                        "• Upload a video with embedded captions/subtitles\n"
                        "• Include a subtitle file with the same name as your video\n"
                        "• Or upload a PDF/text file instead\n\n"
                        "Note: Audio transcription is currently disabled to save resources."
                    )
                    
                    raise Exception(error_msg)
            else:
                # Audio file - would need Whisper transcription
                logger.info("Audio file detected, but audio transcription is disabled")
                raise Exception(
                    "Audio transcription is currently disabled. "
                    "Please upload a video with captions or a text/PDF file instead."
                )

            # Generate metadata
            metadata = self._generate_metadata(filename, text, file_path)
            metadata['extraction_method'] = extraction_method

            return text, metadata

        finally:
            # Clean up any temporary files
            pass

    def process_file(self, file_obj, filename: str, model_size: str = "base") -> Tuple[str, Dict[str, Any]]:
        """
        Process uploaded audio/video file and extract text

        Args:
            file_obj: File object from Flask request
            filename: Original filename
            model_size: Whisper model size

        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not self.is_supported_file(filename):
            raise Exception(f"Unsupported file format. Supported formats: {self.supported_audio_formats | self.supported_video_formats}")

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            file_obj.save(temp_path)

        try:
            # If it's a video file, extract audio first
            if self.is_video_file(filename):
                audio_temp_path = temp_path + "_audio.mp3"
                if not self.extract_audio_from_video(temp_path, audio_temp_path):
                    raise Exception("Failed to extract audio from video file")

                # Use the extracted audio for transcription
                transcription_path = audio_temp_path
            else:
                # Audio file - use directly
                transcription_path = temp_path

            # Extract text using Whisper
            text = self.extract_text_from_audio_video(transcription_path, model_size)

            # Generate metadata
            metadata = self._generate_metadata(filename, text, transcription_path)

            return text, metadata

        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_path)
                if self.is_video_file(filename):
                    audio_temp_path = temp_path + "_audio.mp3"
                    if os.path.exists(audio_temp_path):
                        os.unlink(audio_temp_path)
            except OSError:
                pass  # Ignore cleanup errors

    def _generate_metadata(self, filename: str, text: str, file_path: str) -> Dict[str, Any]:
        """Generate metadata for the processed file"""
        import time

        metadata = {
            'title': os.path.splitext(filename)[0],
            'filename': filename,
            'file_type': 'video' if self.is_video_file(filename) else 'audio',
            'duration': self._get_file_duration(file_path),
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'text_length': len(text),
            'processing_time': time.time(),
            'language': 'English (auto-detected)',
            'model_used': 'OpenAI Whisper'
        }

        return metadata

    def _get_file_duration(self, file_path: str) -> Optional[float]:
        """Get duration of audio/video file in seconds"""
        try:
            if self.moviepy_available:
                import moviepy
                if self.is_video_file(file_path):
                    clip = moviepy.VideoFileClip(file_path)
                    duration = clip.duration
                    clip.close()
                    return duration
                else:
                    # For audio files
                    audio = moviepy.AudioFileClip(file_path)
                    duration = audio.duration
                    audio.close()
                    return duration
            else:
                # Try using ffprobe
                try:
                    cmd = [
                        'ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', file_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        import json
                        data = json.loads(result.stdout)
                        duration = float(data['format']['duration'])
                        return duration
                except:
                    pass

        except Exception as e:
            logger.warning(f"Could not determine file duration: {e}")

        return None

    def validate_file(self, file_obj, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded audio/video file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            if not self.is_supported_file(filename):
                return False, f"Unsupported file format. Supported: {', '.join(self.supported_audio_formats | self.supported_video_formats)}"

            # Check file size (max 500MB for audio/video)
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            file_obj.seek(0)

            if file_size == 0:
                return False, "File is empty"

            if file_size > 500 * 1024 * 1024:  # 500MB limit
                return False, "File is too large (max 500MB)"

            # Try to read file header to validate format
            file_obj.seek(0)
            header = file_obj.read(12)
            file_obj.seek(0)

            if not self._validate_file_header(header, filename):
                return False, "File format validation failed"

            return True, "File is valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_file_header(self, header: bytes, filename: str) -> bool:
        """Basic file header validation"""
        try:
            if self.is_audio_file(filename):
                # MP3: ID3 or ÿû
                if header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                    return True
                # WAV: RIFF
                if header.startswith(b'RIFF'):
                    return True
                # FLAC: fLaC
                if header.startswith(b'fLaC'):
                    return True
                # OGG: OggS
                if header.startswith(b'OggS'):
                    return True

            elif self.is_video_file(filename):
                # MP4: ftyp
                if b'ftyp' in header:
                    return True
                # AVI: RIFF
                if header.startswith(b'RIFF'):
                    return True
                # MOV: wide or mdat
                if header.startswith(b'wide') or b'mdat' in header:
                    return True
                # WebM: EBML header (1A 45 DF A3)
                if header.startswith(b'\x1a\x45\xdf\xa3'):
                    return True
                # MKV: EBML header (same as WebM)
                if header.startswith(b'\x1a\x45\xdf\xa3'):
                    return True
                # FLV: FLV header
                if header.startswith(b'FLV'):
                    return True

            return False

        except:
            return False