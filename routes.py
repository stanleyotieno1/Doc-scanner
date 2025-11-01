from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import select, delete
from database import engine, UploadedFile as DBUploadedFile
from services import extract_from_pdf
from datetime import datetime
import json

router = APIRouter()


@router.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    """
    Extract data from PDF and store in database
    """
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        # Create database record
        db_file = DBUploadedFile(
            filename=file.filename,
            file_size=len(pdf_bytes),
            file_type=file.content_type or "application/pdf",
            status="uploading",
            upload_time=datetime.utcnow()
        )
        
        # Insert into database
        with engine.connect() as conn:
            result = conn.execute(
                DBUploadedFile.__table__.insert().values(
                    filename=db_file.filename,
                    file_size=db_file.file_size,
                    file_type=db_file.file_type,
                    status=db_file.status,
                    upload_time=db_file.upload_time
                )
            )
            conn.commit()
            file_id = result.inserted_primary_key[0]
        
        # Extract data from PDF
        extracted = extract_from_pdf(pdf_bytes)
        
        # Update database record with extracted data
        with engine.connect() as conn:
            if extracted.get("success", False):
                conn.execute(
                    DBUploadedFile.__table__.update()
                    .where(DBUploadedFile.__table__.c.id == file_id)
                    .values(
                        status="completed",
                        extracted_data=json.dumps(extracted.get("data", {})),
                        file_content=pdf_bytes  # Optional: store file
                    )
                )
            else:
                conn.execute(
                    DBUploadedFile.__table__.update()
                    .where(DBUploadedFile.__table__.c.id == file_id)
                    .values(
                        status="failed",
                        error_message=extracted.get("error", "Unknown error")
                    )
                )
            conn.commit()
        
        # Get updated record
        with engine.connect() as conn:
            result = conn.execute(
                select(DBUploadedFile).where(DBUploadedFile.id == file_id)
            ).first()
            
            if result:
                return {
                    "id": result.id,
                    "filename": result.filename,
                    "status": result.status,
                    "extracted": extracted,
                    "upload_time": result.upload_time.isoformat()
                }
    
    except Exception as e:
        # Try to update database with error if record was created
        if 'file_id' in locals():
            try:
                with engine.connect() as conn:
                    conn.execute(
                        DBUploadedFile.__table__.update()
                        .where(DBUploadedFile.__table__.c.id == file_id)
                        .values(status="failed", error_message=str(e))
                    )
                    conn.commit()
            except:
                pass
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def get_all_files():
    """
    Get all uploaded files
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                select(DBUploadedFile).order_by(DBUploadedFile.upload_time.desc())
            ).fetchall()
            
            files = []
            for row in result:
                extracted_data = None
                if row.extracted_data:
                    try:
                        extracted_data = json.loads(row.extracted_data)
                    except:
                        extracted_data = None
                
                files.append({
                    "id": row.id,
                    "filename": row.filename,
                    "file_size": row.file_size,
                    "file_type": row.file_type,
                    "status": row.status,
                    "upload_time": row.upload_time.isoformat() if row.upload_time else None,
                    "extracted_data": extracted_data,
                    "error_message": row.error_message
                })
            
            return {"files": files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}")
async def get_file(file_id: int):
    """
    Get specific file by ID
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                select(DBUploadedFile).where(DBUploadedFile.id == file_id)
            ).first()
            
            if not result:
                raise HTTPException(status_code=404, detail="File not found")
            
            extracted_data = None
            if result.extracted_data:
                try:
                    extracted_data = json.loads(result.extracted_data)
                except:
                    extracted_data = None
            
            return {
                "id": result.id,
                "filename": result.filename,
                "file_size": result.file_size,
                "file_type": result.file_type,
                "status": result.status,
                "upload_time": result.upload_time.isoformat() if result.upload_time else None,
                "extracted_data": extracted_data,
                "error_message": result.error_message
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """
    Delete file from database
    """
    try:
        with engine.connect() as conn:
            # Check if file exists
            result = conn.execute(
                select(DBUploadedFile).where(DBUploadedFile.id == file_id)
            ).first()
            
            if not result:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Delete the file
            conn.execute(
                delete(DBUploadedFile).where(DBUploadedFile.id == file_id)
            )
            conn.commit()
            
            return {"message": "File deleted successfully", "id": file_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))