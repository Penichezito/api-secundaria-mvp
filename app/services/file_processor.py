import os 
import mimetypes
from pathlib import Path
from PIL import Image
from PyPDF2 import PdfReader
from app.config import config
from app.services.vision_service import VisionService

class FileProcessor:
    """Processador de arquivos com análise local otimizada"""

    # Mapeamento de tipos MIME para categorias
    MIME_PREFIXES = {
        'image/': 'image',
        'video/': 'video',
        'audio/': 'audio',
        'text/': 'text'
    }

    # Mapeamento de tipos MIME EXATOS
    MIME_EXACT = {
        'application/pdf': 'document',
        'application/msword': 'document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
        'application/vnd.ms-excel': 'spreadsheet',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'spreadsheet',
        'application/zip': 'archive',
        'application/x-rar-compressed': 'archive',
        'application/x-7z-compressed': 'archive'
    }

    # Configuração de análise de texto
    TEXT_ANALYSIS_MAP = [
        {
            'exts': ('.py', '.python'),
            'tags': ['code', 'python', 'programming'],
            'check': lambda c: ['script'] if 'import' in c and 'def' in c else []
        },
        {
            'exts': ('.js', '.jsx', '.ts', '.tsx'),
            'tags': ['code', 'javascript', 'programming'],
            'check': lambda c: (
                (['script'] if 'function' in c or 'const' in c else []) + 
                (['react', 'frontend'] if 'react' in c.lower() or 'component' in c.lower() else [])
            )
        },
        {
            'exts': ('.html', '.htm'),
            'tags': ['code', 'html', 'web', 'markup'],
            'check': lambda c: ['webpage'] if '<html' in c.lower() else []
        },
        {
            'exts': ('.css',),
            'tags': ['code', 'css', 'stylesheet', 'design'],
            'check': None
        },
        {
            'exts': ('.java',),
            'tags': ['code', 'java', 'programming'],
            'check': lambda c: ['oop'] if 'class' in c and 'public' in c else []
        },
        {
            'exts': ('.cpp', '.c', '.h', '.hpp'),
            'tags': ['code', 'c++', 'c', 'programming'],
            'check': lambda c: ['native'] if '#include' in c else []
        },
        {
            'exts': ('.php',),
            'tags': ['code', 'php', 'backend', 'web'],
            'check': None
        },
        {
            'exts': ('.sql',),
            'tags': ['code', 'sql', 'database', 'query'],
            'check': None
        },
        {
            'exts': ('.json',),
            'tags': ['data', 'json', 'config'],
            'check': None
        },
        {
            'exts': ('.md', '.markdown'),
            'tags': ['markdown', 'documentation', 'readme'],
            'check': None
        },
        {
            'exts': ('.csv',),
            'tags': ['csv', 'data', 'spreadsheet'],
            'check': None
        }
    ]
    
    # Keywords para PDF
    PDF_KEYWORDS = {
        'invoice': ['invoice', 'fatura', 'pagamento', 'total'],
        'financial': ['financial', 'financeiro', 'contabilidade'],
        'contract': ['contract', 'contrato', 'acordo'],
        'legal': ['legal', 'juridico', 'tribunal'],
        'proposal': ['proposal', 'proposta', 'orçamento'],
        'budget': ['budget', 'orçamento', 'custo'],
        'report': ['report', 'relatório', 'análise'],
        'presentation': ['presentation', 'apresentação', 'slide']
    }

    def __init__(self):
        self.upload_folder = config.UPLOAD_FOLDER
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.vision_service = VisionService()

    def save_file(self, file, filename):
        """Salva o arquivo no disco e retorna o caminho"""
        file_path = self.upload_folder / filename
        file.save(str(file_path))
        return str(file_path)
    
    def get_file_type(self, filename):
        """Retorna o tipo MIME do arquivo"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stram"
    
    def get_file_category(self, mime_type):
        """Categoriza o arquivo usando lookups em dicionários"""
        # Verifica correspondência exata
        if mime_type in self.MIME_EXACT:
            return self.MIME_EXACT[mime_type]
        
        # Verifica prefixos
        for prefix, category in self.MIME_PREFIXES.items():
            if mime_type.startswith(prefix):
                return category
            
        return "other"
    
    def analyze_file(self, file_path, mime_type):
        """"Analisa arquivo e retorna tags apropriadas"""
        category = self.get_file_category(mime_type)

        # Mapeamento de categoria para método de análise
        analyzer_map = {
            "image": self.analyze_image_local,
            "document": self.analyze_pdf,
            "text": self.analyze_text,
            "video": self.analyze_video,
            "audio": self.analyze_audio
        }

        analyzer = analyzer_map.get(category)
        if analyzer:
            return analyzer(file_path)
        
        return [category]

    def analyze_image_local(self, file_path):
        """Análise otimizada de imagem (local + VisionService se API estiver disponível)"""
        try:
            # Análise local básica
            with Image.open(file_path) as img:
                width, height = img.size
                tags = ["image"]

                if img.format:
                    tags.append(img.format.lower())

                # Análise de proporção
                ratio = width / height if height > 0 else 1
                if 0.9 <= ratio <= 1.1:
                    tags.extend(["square", "balanced"])
                elif ratio > 1.5:
                    tags.extend(["landscape", "wide"])
                elif ratio < 0.7:
                    tags.extend(["portrait", "vertical"])

                # Análise de resolução
                pixels = width * height
                if pixels >= 8294400:  # 3840x2160
                    tags.extend(["4k", "ultra-hd"])
                elif pixels >= 2073600:  # 1920x1080
                    tags.extend(["high resolution", "hd"])
                elif pixels >= 480000: # 800x600
                    tags.extend(["low resolution", "sd"])
                
                # Mapeamento de modos de cores
                mode_map = {
                    'RGB': ['color'],
                    'L': ['grayscale', 'black-white'], 
                    'LA': ['grayscale', 'black-white'],
                    'RGBA': ['color', 'transparent']
                }
                tags.extend(mode_map.get(img.mode, []))

                # Análise de cor dominante
                self._analyze_dominant_color(img, tags)
            
            # Integração com Google Cloud Vision API (se disponível)
            if self.vision_service.is_available():
                vision_tags = self.vision_service.analyze_image(file_path)
                if vision_tags:
                    tags.extend(vision_tags)
                    print(f"✓ Google Vision API: {len(vision_tags)} tags adicionadas")
            
            return tags
        except Exception as e:
            print(f"Erro na análise de imagem: {e}")
            return ["image", "unknown"]


    def _analyze_dominant_color(self, img, tags):
        """Extrai cor dominante da imagem"""
        try:
            img_small = img.resize((1, 1))
            color = img_small.getpixel((0, 0))

            if isinstance(color, int):
                return
                
            r, g, b = color[0], color[1], color[2]

            if r > 200 and g < 100 and b < 100:
                tags.append('red')
            elif r < 100 and g > 200 and b < 100:
                tags.append('green')
            elif r < 100 and g < 100 and b > 200:
                tags.append('blue')
            elif r > 200 and g > 200 and b > 200:
                tags.append('bright')
            elif r < 50 and g < 50 and b < 50:
                tags.append('dark')
        except:
            pass
       
    def analyze_pdf(self, file_path):
        """Análise otimizada de PDFs"""
        try:
            with open(file_path, "rb") as file:
                pdf = PdfReader(file)
                num_pages = len(pdf.pages)
                tags = ["pdf", "document"]

                # Categorização por tamanho
                if num_pages <= 3:
                    tags.extend(["single-page", "flyer"])
                elif num_pages <= 5:
                    tags.extend(["short-document", "brief"])
                elif num_pages <= 20:
                    tags.extend(["medium-document", "report"])
                else:
                    tags.extend(["long-document", "book", "manual"])

                # Extração de texto e vericação de palavras-chave(keywords)
                text_sample = "".join([p.extract_text() for p in pdf.pages[:3]]).lower()

                if text_sample:
                    if len(text_sample.split()) > 1000:
                        tags.append("text-heavy")

                    # Busca eficiente por categorias 
                    found_categories = {
                        category for category, keywords in self.PDF_KEYWORDS.items()
                        if any(k in text_sample for k in keywords)
                    }
                    tags.extend(list(found_categories))

            return tags
        except Exception as e:
            print(f"Erro na análise de PDF: {e}")
            return ["pdf", "document", "error"]

    
    def analyze_text(self, file_path):
        """Análise otimizada de arquivos de texto"""
        try:
            file_lower = file_path.lower()
            tags = ["text"]

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read(10000)

                # Itera sobre configurações de análise
                for config in self.TEXT_ANALYSIS_MAP:
                    if any(file_lower.endswith(ext) for ext in config["exts"]):
                        tags.extend(config["tags"])
                        if config["check"]:
                            tags.extend(config["check"](content))
                        break
                
                if content.count('\n') > 100:
                    tags.append("large-file")

            return tags
        except Exception as e:
            print(f"Erro na análise de texto: {e}")
            return ["text", "error"]
        

    def analyze_video(self, file_path):
        """Análise de arquivos de vídeo"""
        ext_map = {
            '.mp4': ['mp4', 'h264'], 
            '.avi': ['avi'], 
            '.mov': ['mov', 'quicktime'], 
            '.mkv': ['mkv', 'matroska'], 
            '.webm': ['webm', 'vp9']
        }
        return self._analyze_media_ext(file_path, "video", ext_map)


    def analyze_audio(self, file_path):
        """Análise de arquivos de áudio"""
        ext_map = {
             '.mp3': ['mp3', 'mpeg'], 
            '.wav': ['wav', 'lossless'],
            '.flac': ['flac', 'lossless', 'high-quality'],
            '.ogg': ['ogg', 'vorbis'], 
            '.m4a': ['m4a', 'aac']
        }
        return self._analyze_media_ext(file_path, 'audio', ext_map)

    def _analyze_media_ext(self, file_path, base_tag, mapping):
        """Helper genérico para análise de mídia"""
        tags = [base_tag, "media"]
        file_lower = file_path.lower()

        for ext, extras in mapping.items():
            if file_lower.endswith(ext):
                tags.extend(extras)
                break
        
        return tags


