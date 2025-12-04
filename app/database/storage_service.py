from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column

from app.config import config
from typing import List, Optional

Base = declarative_base()
engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
SessionLocal = sessionmaker(bind=engine)

class FileModel(Base):
    """Modelo de arquivo no banco de dados"""
    __tablename__ = "files_secondary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StorageService:
    """Serviço de armazenamento e recuperação de arquivos"""

    def __init__(self) -> None:
        Base.metadata.create_all(bind=engine)

    def get_session(self):
        """Cria nova sessão do banco de dados"""
        return SessionLocal()
    
    def save_file_metadata(self, filename, file_path, file_type, category, tags):
        """Salva metadados arquivo no banco de dados"""
        session = self.get_session()
        try:
            file_record = FileModel(
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                category=category,
                tags=tags
            )
            session.add(file_record)
            session.commit()
            session.refresh(file_record)

            return file_record
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_file_by_id(self, file_id):
        """Busca arquivo pelo ID"""
        session = self.get_session()
        try:
            file_record = session.query(FileModel).filter(FileModel.id == file_id).first()
            return self._to_dict(file_record) if file_record else None
        finally:
            session.close()

    def get_all_files(self):
        """Lista todos os arquivos"""
        session = self.get_session()
        try:
            files = session.query(FileModel).all()
            return [self._to_dict(f) for f in files]
        finally:
            session.close()

    def get_files_by_tags(self, tags):
        """Busca arquivos por tags"""
        session = self.get_session()
        try:
            files = session.query(FileModel).all()
            
            # Filtra arquivos que contêm qualquer uma das tags buscadas
            search_lower = {tag.lower() for tag in tags}
            matching_files = [
                f for f in files
                if any(tag.lower() in search_lower for tag in f.tags)
            ]
            
            return [self._to_dict(f) for f in matching_files]
        finally:
            session.close()

    def get_files_by_category(self, category):
        """Busca arquivos por categoria"""
        session = self.get_session()
        try:
            files = session.query(FileModel).filter(
                FileModel.category == category
            ).all()
            return [self._to_dict(f) for f in files]
        finally:
            session.close()
    
    def update_file_tags(self, file_id, new_tags):
        """Atualiza tags de um arquivo"""
        session = self.get_session()
        try:
            file_record = session.query(FileModel).filter(FileModel.id == file_id).first()

            if not file_record:
                return None
            
            file_record.tags = new_tags
            file_record.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(file_record)

            return self._to_dict(file_record)
        
        except Exception as e:
            session.rollback()
            raise e 
        finally:
            session.close()

    def delete_file(self, file_id):
        """Remove arquivo do banco"""
        session = self.get_session()
        try:
            file_record = session.query(FileModel).filter(FileModel.id == file_id).first()
            
            if not file_record:
                return False
            
            session.delete(file_record)
            session.commit()
            
            return True
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_statistics(self):
        """Retorna estatísticas gerais"""
        session = self.get_session()
        try:
            total_files = session.query(FileModel).count()

            # Conta arquivos por categoria
            categories = {}
            for file in session.query(FileModel.category).all():
                cat = file.category
                categories[cat] = categories.get(cat, 0) + 1
        
            # Conta tags mais usadas
            tag_count = {}
            for file in session.query(FileModel).all():
                for tag in file.tags:
                    tag_lower = tag.lower()
                    tag_count[tag_lower] = tag_count.get(tag_lower, 0) + 1

            top_tags = sorted(
                tag_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            return {
                "total_files": total_files,
                "categories": categories,
                "top_tags": dict(top_tags)
            }
        finally:
            session.close()

    def _to_dict(self, file_record):
        """Converte modelo para dicionário"""
        if not file_record:
            return None
            
        return {
            'id': file_record.id,
            'filename': file_record.filename,
            'file_path': file_record.file_path,
            'file_type': file_record.file_type,
            'category': file_record.category,
            'tags': file_record.tags,
            'created_at': file_record.created_at.isoformat(),
            'updated_at': file_record.updated_at.isoformat()
        }