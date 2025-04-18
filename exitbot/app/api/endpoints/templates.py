"""
API endpoints for managing interview templates.
"""
import logging
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.api import deps
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/", 
    response_model=schemas.TemplateList,
    summary="List interview templates",
    description="""
    Retrieve a list of all interview templates.
    Different template types are available for different interview purposes.
    Results can be filtered by interview type and active status.
    """,
    response_description="List of interview templates",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"}
    }
)
async def list_templates(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="Number of items to skip", ge=0),
    limit: int = Query(100, description="Maximum number of items to return", le=1000),
    interview_type: Optional[schemas.InterviewType] = Query(
        None, 
        description="Filter by interview type"
    ),
    is_active: Optional[bool] = Query(
        None, 
        description="Filter by active status"
    )
) -> schemas.TemplateList:
    """
    List interview templates with filtering options.
    
    Parameters:
    - skip: Number of items to skip for pagination
    - limit: Maximum number of items to return
    - interview_type: Optional filter by interview type
    - is_active: Optional filter by active status
    
    Returns:
    - List of interview templates
    """
    # Build filters
    filters = {}
    if interview_type:
        filters["interview_type"] = interview_type
    if is_active is not None:
        filters["is_active"] = is_active
    
    # Get templates
    total = crud.template.count(db, filters=filters)
    templates = crud.template.get_multi(
        db, skip=skip, limit=limit, filters=filters
    )
    
    logger.info(f"Retrieved {len(templates)} templates for user {current_user.id}")
    return {"total": total, "items": templates}


@router.post(
    "/", 
    response_model=schemas.InterviewTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Create new template",
    description="""
    Create a new interview template.
    Templates define the structure, prompts, and questions for interview types.
    Only admin users can create templates.
    """,
    response_description="Created template",
    responses={
        201: {"description": "Template successfully created"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        422: {"description": "Validation error in template data"}
    }
)
async def create_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: schemas.TemplateCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.InterviewTemplate:
    """
    Create a new interview template.
    
    Parameters:
    - template_in: Template creation data
    
    Returns:
    - Created template object
    """
    # Check if template with same name already exists
    existing = crud.template.get_by_name(db, name=template_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this name already exists"
        )
    
    # Create template
    template = crud.template.create_with_owner(
        db=db, obj_in=template_in, owner_id=current_user.id
    )
    
    logger.info(f"Template {template.id} created by user {current_user.id}")
    return template


@router.get(
    "/{template_id}", 
    response_model=schemas.InterviewTemplate,
    summary="Get template by ID",
    description="""
    Retrieve a specific interview template by ID.
    Templates contain the structure and prompts for conducting interviews.
    """,
    response_description="Template details",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        404: {"description": "Template not found"}
    }
)
async def get_template(
    template_id: int = Path(..., description="The ID of the template to retrieve", ge=1),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> schemas.InterviewTemplate:
    """
    Get a specific template by ID.
    
    Parameters:
    - template_id: ID of the template to retrieve
    
    Returns:
    - Template object
    
    Raises:
    - HTTPException 404: If template not found
    """
    template = crud.template.get(db, id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.put(
    "/{template_id}", 
    response_model=schemas.InterviewTemplate,
    summary="Update template",
    description="""
    Update an existing interview template.
    Only admin users can update templates.
    """,
    response_description="Updated template",
    responses={
        200: {"description": "Template successfully updated"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "Template not found"},
        422: {"description": "Validation error in update data"}
    }
)
async def update_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int = Path(..., description="The ID of the template to update", ge=1),
    template_in: schemas.TemplateUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.InterviewTemplate:
    """
    Update a template.
    
    Parameters:
    - template_id: ID of the template to update
    - template_in: Template update data
    
    Returns:
    - Updated template object
    
    Raises:
    - HTTPException 404: If template not found
    - HTTPException 400: If update would create name conflict
    """
    template = crud.template.get(db, id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check for name conflicts if name is being updated
    if template_in.name and template_in.name != template.name:
        existing = crud.template.get_by_name(db, name=template_in.name)
        if existing and existing.id != template_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template with this name already exists"
            )
    
    # Update template
    updated_template = crud.template.update(
        db=db, db_obj=template, obj_in=template_in
    )
    
    logger.info(f"Template {template_id} updated by user {current_user.id}")
    return updated_template


@router.delete(
    "/{template_id}", 
    response_model=schemas.InterviewTemplate,
    summary="Delete template",
    description="""
    Delete an interview template.
    Only admin users can delete templates.
    """,
    response_description="Deleted template",
    responses={
        200: {"description": "Template successfully deleted"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "Template not found"}
    }
)
async def delete_template(
    template_id: int = Path(..., description="The ID of the template to delete", ge=1),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.InterviewTemplate:
    """
    Delete a template.
    
    Parameters:
    - template_id: ID of the template to delete
    
    Returns:
    - Deleted template object
    
    Raises:
    - HTTPException 404: If template not found
    """
    template = crud.template.get(db, id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Delete template
    template = crud.template.remove(db=db, id=template_id)
    
    logger.info(f"Template {template_id} deleted by user {current_user.id}")
    return template


@router.get(
    "/types", 
    response_model=List[dict],
    summary="Get available template types",
    description="""
    Retrieve a list of available interview template types.
    Each type is designed for a specific kind of interview.
    """,
    response_description="List of template types",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"}
    }
)
async def get_template_types(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> List[dict]:
    """
    Get a list of available template types.
    
    Returns:
    - List of template types with descriptions
    """
    # Return a list of interview types and their descriptions
    template_types = [
        {
            "type": schemas.InterviewType.EXIT.value,
            "name": "Exit Interview",
            "description": "For interviews with departing employees to gather feedback"
        },
        {
            "type": schemas.InterviewType.ONBOARDING.value,
            "name": "Onboarding Interview",
            "description": "For interviews with new employees joining the organization"
        },
        {
            "type": schemas.InterviewType.PERFORMANCE.value,
            "name": "Performance Review",
            "description": "For periodic performance evaluation interviews"
        },
        {
            "type": schemas.InterviewType.SATISFACTION.value,
            "name": "Satisfaction Survey",
            "description": "For general employee satisfaction assessment"
        },
        {
            "type": schemas.InterviewType.CUSTOM.value,
            "name": "Custom Interview",
            "description": "For customized interview types specific to your needs"
        }
    ]
    
    return template_types


@router.post(
    "/{template_id}/clone", 
    response_model=schemas.InterviewTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Clone template",
    description="""
    Create a copy of an existing template that can be modified independently.
    Only admin users can clone templates.
    """,
    response_description="Cloned template",
    responses={
        201: {"description": "Template successfully cloned"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "Template not found"},
        422: {"description": "Validation error in clone data"}
    }
)
async def clone_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int = Path(..., description="The ID of the template to clone", ge=1),
    name: str = Query(..., description="Name for the cloned template", min_length=1),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.InterviewTemplate:
    """
    Clone an existing template.
    
    Parameters:
    - template_id: ID of the template to clone
    - name: Name for the cloned template
    
    Returns:
    - Cloned template object
    
    Raises:
    - HTTPException 404: If template not found
    - HTTPException 400: If template with same name already exists
    """
    # Check if source template exists
    source_template = crud.template.get(db, id=template_id)
    if not source_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source template not found"
        )
    
    # Check if template with new name already exists
    existing = crud.template.get_by_name(db, name=name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this name already exists"
        )
    
    # Create template data from source
    template_data = schemas.TemplateCreate(
        name=name,
        description=f"Clone of {source_template.name}",
        interview_type=source_template.interview_type,
        system_prompt=source_template.system_prompt,
        initial_message=source_template.initial_message,
        questions=source_template.questions
    )
    
    # Create cloned template
    cloned_template = crud.template.create_with_owner(
        db=db, obj_in=template_data, owner_id=current_user.id
    )
    
    logger.info(f"Template {template_id} cloned to {cloned_template.id} by user {current_user.id}")
    return cloned_template 