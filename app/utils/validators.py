from app.config import config

class FileValidator:
    """Validador de arquivos"""

    # Extensões permitidas por categoria
    ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'},
        'document': {'.pdf', '.doc', '.docx', '.txt', '.odt'},
        'spreadsheet': {'.xls', '.xlsx', '.csv', '.ods'},
        'video': {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'},
        'audio': {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'},
        'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'},
        'code': {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', 
            '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', 
            '.rs', '.swift', '.kt', '.sql', '.sh', '.json', '.xml', '.yml', '.yaml'
        }
    }

    # Conjunto completo de todas as extensões permitidas
    ALL_ALLOWED_EXTENSIONS = set().union(*ALLOWED_EXTENSIONS.values())

    # Tipos MIME permitidos
    DANGEROUS_MIME_TYPES = {
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-executable',
        'application/x-sh',
        'application/x-bat'
    }

    @classmethod
    def is_allowed_extension(cls, filename):
        """Verifica se a extensão do arquivo é permitida"""
        if '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        return f".{ext}" in cls.ALL_ALLOWED_EXTENSIONS

    @classmethod
    def is_allowed_size(cls, file):
        """Verifica se o tamanho do arquivo é permitido"""
        file.seek(0, 2) # Move para o final do arquivo
        size = file.tell()
        file.seek(0)   # Retorna ao início do arquivo

        return size <= config.MAX_FILE_SIZE

    @classmethod
    def is_safe_mime_type(cls, mime_type):
        """Verifica se o tipo MIME é perigoso"""
        return mime_type not in cls.DANGEROUS_MIME_TYPES


    @classmethod
    def validate_filename(cls, filename):
        """Valida o nome do arquivo"""
        if not filename or filename.strip() == "":
            return False, "Nome de arquivo vazio."
        
        if len(filename) > 255:
            return False, "Nome de arquivo muito longo."
        
        # Caracteres proibidos
        forbidden_chars = {'/', '\\', '<', '>', ':', '"', '|', '?', '*'}
        if any(char in filename for char in forbidden_chars):
            return False, "Nome de arquivo contém caracteres inválidos."

        return True, None

def validate_file(file):
    """Função principal para validação de arquivo"""

    # Valida nome do arquivo
    is_valid, error = FileValidator.validate_filename(file.filename)
    if not is_valid:
        return False, error
    
    # Valida extensão
    if not FileValidator.is_allowed_extension(file.filename):
        return False, "Extensão de arquivo não permitida."
    
    # Valida tamanho
    if not FileValidator.is_allowed_size(file):
        max_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"Arquivo muito grande. Tamanho máximo: {max_mb} MB."
    
    return True, None