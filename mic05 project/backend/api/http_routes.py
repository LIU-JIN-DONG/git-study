from datetime import datetime
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse,Response
from pathlib import Path

from services.title_service import title_service
from models.language_stats import LanguageStats
from services.websocket_service import websocket_manager
from models.history import History,HistoryPydantic
from utils.exceptions import GPTException
from services.summary_service import summary_service
from config.settings import Settings
from utils.language_utils import normalize_language_code

translate_router = APIRouter()

@translate_router.get("/history")
async def get_history(page:int =1,limit:int =20):
    """
    获取全部历史记录
    """
    try:
        histories = await History.get_all_histories(page,limit)
        
        total= await History.all().count()

        all_histories = await History.all()
        # 统计所有conversation总数
        total_conversation = 0
        for history in all_histories:
            total_conversation += len(history.conversation)

        # 转换每个历史记录为 Pydantic 模型
        history_list = []
        for history in histories:
            history_data = await HistoryPydantic.from_tortoise_orm(history)
            history_list.append(history_data)

        return {
            "code":200,
            "message":"success",
            "data":{
                "total":total,
                "messages":total_conversation,
                "page":page,
                "limit":limit,
                "histories":history_list
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@translate_router.get("/history/{session_id}")
async def get_history_by_session_id(session_id:str,page:int =1,limit:int =20):
    """
    根据会话ID获取历史记录
    """
    try:
        # 优先从内存中获取
        if session_id in websocket_manager.sessions:
            session = websocket_manager.sessions[session_id]
            history = session
        else:
            # 从数据库中获取
            history = await History.get_by_session_id(session_id)

        if not history:
            raise HTTPException(status_code=404,detail="History not found")

        total = len(history.conversation)
        
        # 分页处理
        start = (page - 1) * limit
        end = start + limit
        paginated_records = history.conversation[start:end]

        return {
            "code":200,
            "message":"success",
            "data":{
                "total":total,
                "page":page,
                "limit":limit,
                "records":paginated_records
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@translate_router.post("/export/summary")
async def export_summary(session_id:str,format:str="md",language:str="english"):
    """
    导出会话总结
    """
    try:
        normalized_lang = normalize_language_code(language)
        summary = await summary_service.generate_and_export_summary(session_id,normalized_lang)

        # 获取文件信息
        file_info = summary.get("file_info")
        if not file_info:
            raise HTTPException(status_code=500, detail="Failed to generate export file")
        if not file_info.get("relative_path"):
            raise HTTPException(status_code=500, detail="Failed to generate export file")
        
        # 生成下载链接
        download_url = f"/api/download/summary/{file_info['relative_path']}"

        expires_at = datetime.now().replace(hour=23,minute=59,second=59).isoformat()

        return {
            "code":200,
            "message":"success",
            "data":{
                "download_url":download_url,
                "file_name":file_info.get("filename"),
                "summary":summary.get("summary"),
                "expires_at":expires_at,
                "file_size":file_info.get("size")
            }
        }

    except HTTPException:
        raise
    except GPTException as e:
        raise HTTPException(status_code=500, detail=f"GPT service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 下载文件
@translate_router.get("/download/summary/{file_path}")
async def download_summary(file_path:str):
    """
    下载文件
    """
    try:
        SUMMARY_DIR = Path(Settings.EXPORT_DIR or "./backend/exports").resolve()
        # 检查文件格式
        filename = Path(file_path)
        if not filename.suffix == ".md":
            raise HTTPException(status_code=400, detail="Invalid file format!!Only .md files are supported")

        requested_path = SUMMARY_DIR / filename
        requested_path = requested_path.resolve()
        
        # 检查文件是否在导出目录下
        if not requested_path.is_relative_to(SUMMARY_DIR):
            raise HTTPException(status_code=403, detail="Access denied")

        # 优先从文件系统提取文件
        if requested_path.is_file():
            return FileResponse(requested_path.as_posix(),filename=filename.name)
        
        # 如果文件不存在，则从数据库中获取
        session_id = file_path.replace(".md","").split("_")[-1]
        session_id = f"session_{session_id}"
        history = await History.get_by_session_id(session_id)
        if not history or not history.summary:
            raise HTTPException(status_code=404, detail="File not found and no summary in database")
        
        # 返回为md文件
        return Response(
            content=history.summary,
            media_type="text/markdown",
            headers={
                "Content-Disposition":f"attachment; filename={filename.name}",
                "Content-Type":"text/markdown; charset=utf-8"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@translate_router.post("/language/switch")
async def switch_language(session_id:str,language:str,auto_retranslate:bool=False):
    """
    切换目标语言
    """
    try:
        normalized_lang = normalize_language_code(language)

        # 获取会话
        session = websocket_manager.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 记录之前的语言
        previous_language = session.target_lang

        # 更新会话语言
        session.update_target_lang(normalized_lang)

        # 如果auto_retranslate为True，则重新翻译
        if auto_retranslate and session.conversation:
            last_conversation = session.conversation[-1]
            last_transcript = last_conversation.get("transcript")
            last_source_lang = last_conversation.get("source_lang")

            if last_transcript and last_source_lang:
                # 调用翻译服务
                from services.translation_service import translation_service

                retranslated_text = await translation_service.translate(
                    session,
                    last_transcript,
                    normalized_lang,
                    ''
                )

                if retranslated_text:
                    # 更新会话
                    last_conversation["transcript"] = retranslated_text.get("target_text")
                    last_conversation["target_lang"] = normalized_lang

        return {
            "code":200,
            "message":"success",
            "data":{
                "session_id":session_id,
                "previous_language":previous_language,
                "current_language":normalized_lang,
                "retranslated_text":retranslated_text.get("target_text","") 
            }
        }


          
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@translate_router.put("/title/update/{session_id}")
async def update_session_title(session_id:str):
    """
    更新会话标题
    """
    try:
        await title_service.generate_title(session_id)
        
        return {
            "code":200,
            "message":"success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@translate_router.get("/session/{category}")
async def get_sessions_by_category(category:str):
    """
    根据会话分类获取会话
    """
    try:
        histories = await History.get_by_category(category)
        # 使用列表推导式
        history_list = [
            await HistoryPydantic.from_tortoise_orm(history) 
            for history in histories
        ]

        return {
            "code":200,
            "message":"success",
            "data":{
                "histories":history_list
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

# 其他接口
@translate_router.get("/language/stats")
async def get_language_stats():
    """
    获取语言统计
    """
    try:
        languages= await LanguageStats.get_all_languages()
        top_language = await LanguageStats.get_top_language()

        return {
            "code":200,
            "message":"success",
            "data":{
                "languages":languages,
                "top_language":top_language
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@translate_router.get("/session/active")
async def get_active_sessions():
    """
    获取活跃会话
    """
    try:
        active_sessions = websocket_manager.get_active_sessions()

        return {
            "code":200,
            "message":"success",
            "data":{
                "active_sessions":active_sessions,
                "total_sessions":len(active_sessions)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# 获取会话分类
@translate_router.get("/categories")
async def get_session_categories():
    """
    获取会话分类
    """
    categories = [
        "Casual",
        "Travel",
        "Business",
        "Shopping",
        "Food",
        "Entertainment",
        "Education",
        "Technology",
        "Medical",
        "Legal",
        "Emergency"
    ]
    return {
        "code":200,
        "message":"success",
        "data":{
            "categories":categories
        }
    }
