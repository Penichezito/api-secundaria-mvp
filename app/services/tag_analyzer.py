from app.config import config

class TagAnalyzer:
    """Gerenciador de tags com filtragem e normalização"""
    

    # Taghs comuns que podem ser removidas
    COMMON_TAGS_TO_REMOVE = {
        'unknown', 'error', 'other', 'undefined'
    }

    # Mapeamento de sinônimos para normalização
    TAG_SYNONYMS = {
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
        'png': 'png',
        'gif': 'gif',
        'pic': 'image',
        'picture': 'image',
        'photo': 'image',
        'img': 'image',
        'movie': 'video',
        'clip': 'video',
        'sound': 'audio',
        'music': 'audio',
        'doc': 'document',
        'paper': 'document',
        'file': 'document',
        'code': 'programming',
        'script': 'programming',
        'dev': 'development',
        'frontend': 'front-end',
        'backend': 'back-end'
    }
    
    # Prioridade de tags para ordenação
    TAG_PRIORITY = {
        'image': 10,
        'video': 10,
        'audio': 10,
        'document': 10,
        'code': 9,
        'programming': 9,
        'python': 8,
        'javascript': 8,
        'react': 8,
        'high-resolution': 7,
        '4k': 7,
        'hd': 7,
        'pdf': 6,
        'web': 5,
        'frontend': 5,
        'backend': 5
    }   

    def __init__(self):
        self.min_confidence = config.MIN_TAG_CONFIDENCE
        self.max_tags = config.MAX_TAGS_PER_FILE

    def normalize_tags(self, tags):
        """Normaliza e filtra tags usando dicionários de sinônimos"""
        normalized = []

        for tag in tags:
            tag_lower = tag.lower()
            # Aplica sinônimo se existir
            normalized_tag = self.TAG_SYNONYMS.get(tag_lower, tag_lower)
            normalized.append(normalized_tag)
        
        return normalized
    
    def filter_tags(self, tags):
        """Remove tags indesejadas e duplicadas"""
        # Remove duplicatas mantendo ordem
        seen = set()
        filtered = []

        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower not in seen and tag_lower not in self.COMMON_TAGS_TO_REMOVE:
                seen.add(tag_lower)
                filtered.append(tag_lower)

        return filtered
    
    def prioritize_tags(self, tags):
        """Ordena tags com base na prioridade definida e limita quantidade"""
        # Ordena usando prioridade (maior primeiro) e alfabeticamente como desempate
        sorted_tags = sorted(
            tags,
            key=lambda t: (self.TAG_PRIORITY.get(t, 0), t),
            reverse=True
        )

        # Limita ao máximo configurado
        return sorted_tags[:self.max_tags]
    
    def process_tags(self,raw_tags):
        """Pipeline completo de processamento de tags"""
        # 1. Normaliza tags
        normalized = self.normalize_tags(raw_tags)

        # 2. Filtra tags
        filtered = self.filter_tags(normalized)

        # 3. Prioriza tags e as limita
        final = self.prioritize_tags(filtered)

        return final
    
    def merge_tags(self, *tag_lists):
        """Mescla múltiplas listas de tags, removendo duplicatas e reprocessando"""
        all_tags = []
        for tags in tag_lists:
            all_tags.extend(tags)

        return self.process_tags(all_tags)
    
    def add_custom_tags(self, existing_tags, custom_tags):
        """Adiciona tags customizadas às existentes e reprocessa"""
        return self.merge_tags(existing_tags, custom_tags)
    
    def search_by_tags(self, search_tags, file_tags):
        """"Verifica se o arquivo corresponde aos critérios de busca"""
        search_lower = {tag.lower() for tag in search_tags}
        file_lower = {tag.lower() for tag in file_tags}

        # Retorna True se qualquer tag de busca está presente
        return bool(search_lower & file_lower)
    
    def get_tag_statistics(self, all_files_tags):
        """Gera estatísticas básicas de uso sobre as tags fornecidas"""
        tag_count = {}

        for file_tags in all_files_tags:
            for tag in file_tags:
                tag_lower = tag.lower()
                tag_count[tag_lower] = tag_count.get(tag_lower, 0) + 1

        # Ordena por frequência
        sorted_stats = dict(sorted(
            tag_count.items(),
            key=lambda item: item[1],
            reverse=True
        ))

        return dict(sorted_stats)

        