from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from app.services.file_processor import FileProcessor
from app.services.tag_analyzer import TagAnalyzer
from app.database.storage_service import StorageService
from app.utils.validators import validate_file

files_bp = Blueprint("file_bp", __name__, url_prefix="/api/files")

# Inicializa serviços
file_processor = FileProcessor()
tag_analyzer = TagAnalyzer()
storage_service = StorageService()  

@files_bp.route("/process", methods=["POST"])
def process_file():
    """Processa upload de arquivo e gera tags automaticamente"""
    try:
        # Validação do arquivo
        if "file" not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado."}), 400
        
        file = request.files["file"]
        if file.filename is None or file.filename == "":
            return jsonify({"error": "Nome de arquivo vazio."}), 400
        
        # Valida o arquivo
        is_valid, error_message = validate_file(file)
        if not is_valid:
            return jsonify({"error": error_message}), 400
        
        # Gera nome seguro
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{original_filename}"

        # Salva o arquivo 
        file_path = file_processor.save_file(file, filename)

        # Processa o arquivo
        mime_type = file_processor.get_file_type(filename)
        category = file_processor.get_file_category(mime_type)
        raw_tags = file_processor.analyze_file(file_path, mime_type)

        # Processa tags
        final_tags = tag_analyzer.process_tags(raw_tags)

        # Armazena informações no banco de dados
        file_data = storage_service.save_file_metadata(
            filename=filename,
            file_path=file_path,
            file_type=mime_type,
            category=category,
            tags=final_tags
        )

        return jsonify({
            "message": "Arquivo processado com sucesso.",
            "file_id": file_data["id"],
            "file_path": file_path,
            "category": category,
            "tags": final_tags,
            "created_at": file_data["created_at"]
        }), 201
    
    except Exception as e:
        return jsonify({"error": f"Erro ao processar o arquivo: {str(e)}"}), 500

@files_bp.route("/<int:file_id>/tags", methods=["GET"])
def get_file_tags(file_id):
    """Retorna tags de um arquivo específico"""
    try: 
        file_data = storage_service.get_file_by_id(file_id)

        if not file_data:
            return jsonify({"error": "Arquivo não encontrado."}), 404
        
        return jsonify({
            "file_id": file_data["id"],
            "file_name": file_data["filename"],
            "tags": file_data["tags"]   
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar tags: {str(e)}"}), 500
    
@files_bp.route("/<int:file_id>/tags", methods=["PUT"])
def update_file_tags(file_id):
    """Atualiza tags de um arquivo específico"""
    try:
        data = request.get_json()

        if "tags" not in data:
            return jsonify({"error": "Tags não fornecidas."}), 400
        
        new_tags = data["tags"]
        if not isinstance(new_tags, list):
            return jsonify({"error": "Tags devem ser uma lista."}), 400
        
        # Processa novas tags
        processed_tags = tag_analyzer.process_tags(new_tags)

        # Atualiza no banco de dados
        file_data = storage_service.update_file_tags(file_id, processed_tags)

        if not file_data:
            return jsonify({"error": "Arquivo não encontrado."}), 404
        
        return jsonify({
            "messsage": "Tags atualizadas com sucesso.",
            "file_id": file_data["id"],
            "tags": file_data["tags"]       
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro ao atualizar tags: {str(e)}"}), 500
    
@files_bp.route("/search", methods=["POST"])
def search_files():
    """Busca arquivos por tags"""
    try:
        data = request.get_json()

        if "tags" not in data:
            return jsonify({"error": "Tags não fornecidas."}), 400
        
        search_tags = data["tags"]
        if not isinstance(search_tags, list):
            return jsonify({"error": "Tags devem ser uma lista."}), 400
        
        # Busca arquivos no banco de dados
        files = storage_service.get_files_by_tags(search_tags)

        return jsonify({
            "count": len(files),
            "search_tags": search_tags,
            "files": files
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro na busca de arquivos: {str(e)}"}), 500
    
@files_bp.route("", methods=["GET"])
def list_files():
    """Lista todos os arquivos"""
    try:
        category = request.args.get("category")
        
        if category:
            files = storage_service.get_files_by_category(category)
        else:
            files = storage_service.get_all_files()
        
        return jsonify({
            "count": len(files),
            "files": files
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro ao listar arquivos: {str(e)}"}), 500
    
@files_bp.route("/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    """Deleta um arquivo específico"""
    try:
        # Busca arquivo para obter o path
        file_data = storage_service.get_file_by_id(file_id)

        if not file_data:
            return jsonify({"error": "Arquivo não encontrado."}), 404
        
        # Remove arquivo do disco
        if os.path.exists(file_data["file_path"]):
            os.remove(file_data["file_path"])
        
        # Remove do banco de dados
        success = storage_service.delete_file(file_id)

        if success:
            return jsonify({
                "message": "Arquivo removido com sucesso.",
                "file_id": file_id
            }), 200
        else:
            return jsonify({"error": "Erro ao remover o arquivo."}), 500

    except Exception as e:
        return jsonify({"error": f"Erro ao remover o arquivo: {str(e)}"}), 500

@files_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """Retorna estatísticas de arquivos"""
    try:
        stats = storage_service.get_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500
    
@files_bp.route("/health", methods=["GET"])
def health_check():
    """Verifica a saúde da API"""
    return jsonify({
        "status": "ok", 
        "message": "Serviço de arquivos está funcionando."
    }), 200
    
   









































