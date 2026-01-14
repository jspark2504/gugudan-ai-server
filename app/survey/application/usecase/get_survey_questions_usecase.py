from __future__ import annotations
import os
from app.survey.application.port.survey_repository_port import SurveyRepositoryPort


class GetSurveyQuestionsUseCase:

    def __init__(self, survey_repo: SurveyRepositoryPort):
        self._survey_repo = survey_repo

    def execute(self, user_id: int) -> dict:
        # 1) 활성 템플릿 조회
        payload = self._survey_repo.get_active_template_payload()
        if not payload:
            return {"show": False, "reason": "no_active_template"}

        if not payload.get("questions"):
            return {"show": False, "reason": "invalid_payload"}

        template_version = payload.get("version")

        # 2) 이미 응답했으면 show=false
        if self._survey_repo.has_user_responded(user_id=user_id, template_version=template_version):
            return {"show": False, "reason": "already_responded"}

        # 4) 보여준다
        return {
            "show": True,
            "title": payload.get("title"),
            "subtitle": payload.get("subtitle"),
            "footer": payload.get("footer"),
            "version": template_version,
            "questions": payload.get("questions"),
        }
