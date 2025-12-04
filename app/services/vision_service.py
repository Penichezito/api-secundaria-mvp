import os
from typing import Any, List, Dict, Optional
from app.config import config

class VisionService:
    """Serviço de análise de imagens com Google Cloud Vision API"""

    # Mapeamento de features do Vision API
    VISION_FEATURES = {
        "LABEL_DETECTION": {"max_results": 10},
        "IMAGE_PROPERTIES": {},
        "SAFE_SEARCH_DETECTION": {},
        "TEXT_DETECTION": {"max_results": 5},
    }

    # Mapeamento de cores para nomes
    COLOR_NAMES = {
        (255, 0, 0): 'red',
        (0, 255, 0): 'green',
        (0, 0, 255): 'blue',
        (255, 255, 0): 'yellow',
        (255, 165, 0): 'orange',
        (128, 0, 128): 'purple',
        (255, 192, 203): 'pink',
        (0, 0, 0): 'black',
        (255, 255, 255): 'white',
        (128, 128, 128): 'gray'        
    }

    # Categorias de labels para simplificação
    LABEL_CATEGORIES = {
        'nature': ['sky', 'cloud', 'tree', 'flower', 'grass', 'mountain', 'water', 'ocean', 'beach'],
        'urban': ['building', 'street', 'city', 'architecture', 'road', 'car', 'vehicle'],
        'people': ['person', 'face', 'portrait', 'people', 'crowd', 'group'],
        'indoor': ['room', 'furniture', 'interior', 'home', 'office', 'kitchen'],
        'food': ['food', 'dish', 'meal', 'cuisine', 'dessert', 'drink', 'restaurant'],
        'technology': ['computer', 'phone', 'screen', 'device', 'electronic', 'technology'],
        'animal': ['animal', 'pet', 'dog', 'cat', 'bird', 'wildlife'],
        'sport': ['sport', 'game', 'athlete', 'competition', 'exercise', 'fitness']
    }

    def __init__(self):
        self.enabled = config.GOOGLE_CLOUD_VISION_ENABLED
        self.client: Any = None
        
        if self.enabled:
            try:
                from google.cloud import vision
                if config.GOOGLE_APPLICATION_CREDENTIALS:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_APPLICATION_CREDENTIALS
                self.client = vision.ImageAnnotatorClient()
            except ImportError:
                print("⚠️  Google Cloud Vision library not installed. Install with: pip install google-cloud-vision")
                self.enabled = False
            except Exception as e:
                print(f"⚠️  Google Cloud Vision initialized failed: {e}")
                self.enabled = False


    def is_available(self) -> bool:
        """Verifica se o serviço está disponível"""
        return self.enabled and self.client is not None
    
    
    def analyze_image(self, image_path: str) -> List[str]:
        """Analisa imagem usando o Google Cloud Vision API e retorna tags"""
        if not self.is_available():
            return []
        
        try:
            with open(image_path, "rb") as image_file:
                content = image_file.read()

                from google.cloud import vision
                image = vision.Image(content=content)

                # Executa todas as análises em paralelo
                tags = []

                # 1. Detecção de labels
                tags.extend(self._analyze_labels(image))
                
                # 2. Propriedades da imagem (cores)
                tags.extend(self._analyze_colors(image))
                
                # 3. Detecção de texto
                tags.extend(self._analyze_text(image))
                
                # 4. Safe Search (conteúdo)
                tags.extend(self._analyze_safe_search(image))
                
                return tags
            
        except Exception as e:
            print(f"⚠️  Erro na análise com Vision API: {e}")
            return []
        
        
    def _analyze_labels(self, image) -> List[str]:
        """Analisa labels/categorias da imagem"""
        try:
            response = self.client.label_detection(
                image=image,
                max_results=self.VISION_FEATURES["LABEL_DETECTION"]["max_results"]
            )

            tags = []
            for label in response.label_annotations:
                if label.score >= config.MIN_TAG_CONFIDENCE:
                    # Adicione o label original
                    tag = label.description.lower().replace(" ", "-")
                    tags.append(tag)

                    # Adiciona categoria se aplicável 
                    category = self._get_label_category(label.description.lower())
                    if category:
                        tags.append(category)

            return tags
        except Exception as e:
            print(f"Erro na detecção de labels: {e}")
            return []
        
    
    def _analyze_colors(self, image) -> List[str]:
        """Analisa cores dominantes da imagem"""
        try:
            response = self.client.image_properties(image=image)

            tags = []
            if response.image_properties_annotation.dominant_colors.colors:
                # Pega as 3 cores mais dominantes
                for color_info in response.image_properties_annotation.dominant_colors.colors[:3]:
                    color = color_info.color
                    rgb = (int(color.red), int(color.green), int(color.blue))

                    # Mapeaia para nome de cor mais próximo
                    color_name = self._get_closest_color_name(rgb)
                    if color_name and color_name not in tags:
                        tags.append(color_name)

            return tags
        except Exception as e:
            print(f"Erro na análise de cores: {e}")
            return []
        
    
    def _analyze_text(self, image) -> List[str]:
        """Analisa texto na imagem"""
        try:
            response = self.client.text_detection(image=image)

            tags = []
            if response.text_annotations:
                tags.append("text-content")

                # Analisa o primeiro bloco de texto (geralmente o mais relevante)
                if len(response.text_annotations) > 0:
                    text = response.text_annotations[0].description.lower()

                    # Identifica documentos específicos
                    doc_keywords = {
                        'invoice': 'invoice',
                        'receipt': 'receipt',
                        'contract': 'contract',
                        'certificate': 'certificate',
                        'diploma': 'diploma'
                    }

                    for keyword, tag in doc_keywords.items():
                        if keyword in text:
                            tags.append(tag)

                     
            return tags
        except Exception as e:
            print(f"Erro na detecção de texto: {e}")
            return []
        
    
    def _analyze_safe_search(self, image) -> List[str]:
        """Analisa conteúdo de segurança da imagem"""
        try:
            response = self.client.safe_search_detection(image=image)
            safe = response.safe_search_annotation

            # Mapeamento de níveis para tags
            level_map = {
                'VERY_UNLIKELY': None,
                'UNLIKELY': None,
                'POSSIBLE': 'flagged',
                'LIKELY': 'flagged',
                'VERY_LIKELY': 'flagged'
            }

            tags = []

            # Verifica se é conteúdo profissional/seguro
            if (safe.adult.name == "VERY_UNLIKELY" and
                safe.violence.name == "VERY_UNLIKELY"):
                tags.append("professional")
                tags.append("safe-content")

            return tags
        except Exception as e:
            print(f"Erro na análise de Safe Search: {e}")
            return []
        
    
    def _get_label_category(self, label: str) -> Optional[str]:
        """Retorna a categoria de um label, se existir"""
        for category, keywords in self.LABEL_CATEGORIES.items():
            if any(keyword in label for keyword in keywords):
                return category
        return None
    
    def _get_closest_color_name(self, rgb: tuple) -> Optional[str]:
        """Encontra o nome da cor mais próxima"""
        min_distance = float("inf")
        closest_color = None

        for known_rgb, color_name in self.COLOR_NAMES.items():
            # Distância euclidiana no espaço RGB
            distance = sum((a - b) ** 2 for a, b in zip(rgb, known_rgb)) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        # Só retorna se a distância for razoável
        return closest_color if min_distance < 150 else None
    

    def batch_analyze_images(self, image_paths: List[str]) -> Dict[str, List[str]]:
        """Analisa múltiplas imagens em batch"""
        if not self.is_available():
            return {}
        
        results = {}
        for path in image_paths:
            results[path] = self.analyze_image(path)

        return results
    
    def get_usage_info(self) -> Dict:
        """Retorna informações sobre o uso de API"""
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "features": list(self.VISION_FEATURES.keys()),
            "min_confidence": config.MIN_TAG_CONFIDENCE
        }
        
    
        
    


      








































