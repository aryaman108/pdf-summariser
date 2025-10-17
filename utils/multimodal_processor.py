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
            import moviepy.editor as mp

            logger.info(f"Extracting audio from video: {video_path}")
            video = mp.VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()

            logger.info(f"Audio extracted successfully: {audio_path}")
            return True

        except Exception as e:
            logger.error(f"Error extracting audio with MoviePy: {e}")
            return False

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
                import moviepy.editor as mp
                if self.is_video_file(file_path):
                    clip = mp.VideoFileClip(file_path)
                    duration = clip.duration
                    clip.close()
                    return duration
                else:
                    # For audio files
                    audio = mp.AudioFileClip(file_path)
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

            return False

        except:
            return False