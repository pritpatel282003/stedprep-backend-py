from fastapi import APIRouter
from .diagnostic import router as diagnostic_router
from .util import router as util_router
from .student_dashboard import router as student_router
from .study_plan import router as study_plan_router
from .section_test import router as section_test_router
from .full_length_test import router as full_length_router
from .sprint import router as sprint_router

router = APIRouter()
router.include_router(util_router)
router.include_router(diagnostic_router)
router.include_router(student_router)
router.include_router(study_plan_router)
router.include_router(section_test_router)
router.include_router(full_length_router)
router.include_router(sprint_router)
