from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.models.pipeline import ProjectCreate, ProjectState, TaskStatus
from app.services.pipeline_service import pipeline_service
from app.services.project_store import project_store

router = APIRouter()


@router.post("", response_model=ProjectState)
async def create_project(payload: ProjectCreate) -> ProjectState:
    return pipeline_service.create_project(payload)


@router.get("", response_model=list[ProjectState])
async def list_projects() -> list[ProjectState]:
    return project_store.list()


@router.get("/{project_id}", response_model=ProjectState)
async def get_project(project_id: str) -> ProjectState:
    project = project_store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/upload", response_model=ProjectState)
async def upload_video(project_id: str, file: UploadFile = File(...)) -> ProjectState:
    project = project_store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return await pipeline_service.save_upload(project, file)


@router.post("/{project_id}/avatar", response_model=ProjectState)
async def upload_avatar_image(project_id: str, file: UploadFile = File(...)) -> ProjectState:
    project = project_store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return await pipeline_service.save_avatar_image(project, file)


@router.post("/{project_id}/run", response_model=ProjectState)
async def run_project(project_id: str, background_tasks: BackgroundTasks) -> ProjectState:
    project = project_store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    background_tasks.add_task(pipeline_service.run_pipeline, project)
    project.logs.append("流水线任务已提交。")
    return project_store.save(project)


@router.post("/{project_id}/steps/{step_key}/run", response_model=ProjectState)
async def run_project_step(project_id: str, step_key: str, payload: dict[str, Any] | None = None) -> ProjectState:
    project = project_store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload:
        if "douyin_cookie" in payload:
            project.douyin_cookie = str(payload["douyin_cookie"])
        if "douyin_request_url" in payload:
            project.douyin_request_url = str(payload["douyin_request_url"])
        if "rewrite_prompt" in payload:
            project.rewrite_prompt = str(payload["rewrite_prompt"])
        if "cover_title" in payload:
            project.cover_title = str(payload["cover_title"])
    try:
        return await pipeline_service.run_step(project, step_key)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        project.status = TaskStatus.failed
        project.logs.append(str(error))
        project_store.save(project)
        raise HTTPException(status_code=502, detail=str(error)) from error
