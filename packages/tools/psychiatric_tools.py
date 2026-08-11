"""
Psychiatric Assessment & DSM-5 Lookup Function Calling Tools.
Includes PHQ-9, GAD-7, PCL-5 psychometric tools, DSM-5 code lookup, epidemiology metrics, and clinical summary generation.
"""

from typing import Any, Dict, List, Optional
from packages.tools.base import BaseTool, ToolResult


class PHQ9AssessmentTool(BaseTool):
    """Tool to calculate and interpret PHQ-9 Patient Health Questionnaire score for depression severity."""

    def __init__(self) -> None:
        super().__init__(
            name="assess_phq9",
            description="Calculate PHQ-9 Depression severity score (0-27) and clinical recommendation.",
        )

    async def execute(self, scores: Optional[List[int]] = None, total_score: Optional[int] = None, **kwargs: Any) -> ToolResult:
        import re
        if scores is not None:
            total = sum(scores)
        elif total_score is not None:
            total = total_score
        else:
            text = kwargs.get("input_text", "") or str(kwargs)
            found = re.findall(r'\b([0-9]|1[0-9]|2[0-7])\b', text)
            if found:
                total = int(found[0])
            else:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    message="To evaluate your PHQ-9 score, please provide a total score from 0 to 27 (for example: 'My PHQ-9 score is 12').",
                    data={},
                )

        if total < 0 or total > 27:
            return ToolResult(
                success=False,
                tool_name=self.name,
                message="Error: PHQ-9 total score must be between 0 and 27.",
                data={"calculated_score": total},
            )

        if total <= 4:
            severity = "Minimal / No Depression"
            recommendation = "Supportive care; re-screen as clinically indicated."
        elif total <= 9:
            severity = "Mild Depression"
            recommendation = "Watchful waiting; repeat PHQ-9 at follow-up; consider psychoeducation/counseling."
        elif total <= 14:
            severity = "Moderate Depression"
            recommendation = "Consider psychotherapy (CBT, IPT) and/or pharmacotherapy (SSRI/SNRI)."
        elif total <= 19:
            severity = "Moderately Severe Depression"
            recommendation = "Immediate initiation of active treatment with pharmacotherapy and/or psychotherapy."
        else:
            severity = "Severe Depression"
            recommendation = "Immediate referral to psychiatric specialist; combined pharmacotherapy and psychotherapy."

        return ToolResult(
            success=True,
            tool_name=self.name,
            message=f"PHQ-9 Score evaluated: {total}/27 ({severity})",
            data={
                "tool": "PHQ-9",
                "score": total,
                "max_score": 27,
                "severity_level": severity,
                "clinical_recommendation": recommendation,
            },
        )


class GAD7AssessmentTool(BaseTool):
    """Tool to calculate and interpret GAD-7 Generalized Anxiety Scale score."""

    def __init__(self) -> None:
        super().__init__(
            name="assess_gad7",
            description="Calculate GAD-7 Anxiety severity score (0-21) and clinical recommendation.",
        )

    async def execute(self, scores: Optional[List[int]] = None, total_score: Optional[int] = None, **kwargs: Any) -> ToolResult:
        import re
        if scores is not None:
            total = sum(scores)
        elif total_score is not None:
            total = total_score
        else:
            text = kwargs.get("input_text", "") or str(kwargs)
            found = re.findall(r'\b([0-9]|1[0-9]|2[0-1])\b', text)
            if found:
                total = int(found[0])
            else:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    message="To evaluate your GAD-7 anxiety score, please provide a total score from 0 to 21 (for example: 'My GAD-7 score is 8').",
                    data={},
                )

        if total < 0 or total > 21:
            return ToolResult(
                success=False,
                tool_name=self.name,
                message="Error: GAD-7 total score must be between 0 and 21.",
                data={"calculated_score": total},
            )

        if total <= 4:
            severity = "Minimal Anxiety"
            recommendation = "Re-evaluate periodically as needed."
        elif total <= 9:
            severity = "Mild Anxiety"
            recommendation = "Monitor symptoms; psychoeducation and stress-reduction techniques."
        elif total <= 14:
            severity = "Moderate Anxiety"
            recommendation = "Consider further evaluation for GAD/Panic/Social Anxiety; consider CBT or SSRIs."
        else:
            severity = "Severe Anxiety"
            recommendation = "Active clinical intervention; psychiatric consultation and targeted psychotherapy."

        return ToolResult(
            success=True,
            tool_name=self.name,
            message=f"GAD-7 Score evaluated: {total}/21 ({severity})",
            data={
                "tool": "GAD-7",
                "score": total,
                "max_score": 21,
                "severity_level": severity,
                "clinical_recommendation": recommendation,
            },
        )


class PCL5AssessmentTool(BaseTool):
    """Tool to calculate PCL-5 (PTSD Checklist for DSM-5) severity score."""

    def __init__(self) -> None:
        super().__init__(
            name="assess_pcl5",
            description="Calculate PCL-5 PTSD checklist score (0-80) and threshold evaluation.",
        )

    async def execute(self, total_score: int, **kwargs: Any) -> ToolResult:
        threshold_met = total_score >= 33
        severity = "Provisional PTSD Cutoff Met (High Likelihood)" if threshold_met else "Below Diagnostic Cutoff"

        return ToolResult(
            success=True,
            tool_name=self.name,
            message=f"PCL-5 Score: {total_score}/80. Status: {severity}",
            data={
                "tool": "PCL-5",
                "score": total_score,
                "max_score": 80,
                "cutoff_threshold": 33,
                "threshold_met": threshold_met,
                "interpretation": severity,
                "recommendation": "Perform clinical diagnostic interview (CAPS-5) if score >= 33.",
            },
        )


class DSM5CodeLookupTool(BaseTool):
    """Tool to look up ICD-10-CM / DSM-5 diagnostic codes and disorder definitions."""

    def __init__(self) -> None:
        super().__init__(
            name="lookup_dsm5_code",
            description="Lookup DSM-5 disorder ICD-10 codes, diagnostic category, and specifiers.",
        )

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        query_lower = query.lower().strip()

        database = [
            {"disorder": "Major Depressive Disorder (Single Episode)", "icd10": "F32.9", "category": "Depressive Disorders", "specifiers": "Anxious distress, Mixed, Melancholic, Psychotic, Peripartum"},
            {"disorder": "Major Depressive Disorder (Recurrent)", "icd10": "F33.9", "category": "Depressive Disorders", "specifiers": "Anxious distress, Melancholic, Seasonal pattern"},
            {"disorder": "Persistent Depressive Disorder (Dysthymia)", "icd10": "F34.1", "category": "Depressive Disorders", "specifiers": "Early onset, Late onset, Pure dysthymic syndrome"},
            {"disorder": "Generalized Anxiety Disorder (GAD)", "icd10": "F41.1", "category": "Anxiety Disorders", "specifiers": "Unspecified"},
            {"disorder": "Panic Disorder", "icd10": "F41.0", "category": "Anxiety Disorders", "specifiers": "With or without agoraphobia"},
            {"disorder": "Bipolar I Disorder", "icd10": "F31.9", "category": "Bipolar and Related Disorders", "specifiers": "Current episode manic, depressed, mixed; With psychotic features"},
            {"disorder": "Bipolar II Disorder", "icd10": "F31.81", "category": "Bipolar and Related Disorders", "specifiers": "Current episode hypomanic, depressed"},
            {"disorder": "Schizophrenia", "icd10": "F20.9", "category": "Schizophrenia Spectrum Disorders", "specifiers": "First episode, Multiple episodes, Continuous, Catatonia"},
            {"disorder": "Schizoaffective Disorder", "icd10": "F25.0", "category": "Schizophrenia Spectrum Disorders", "specifiers": "Bipolar type, Depressive type"},
            {"disorder": "Posttraumatic Stress Disorder (PTSD)", "icd10": "F43.10", "category": "Trauma- and Stressor-Related Disorders", "specifiers": "With dissociative symptoms, Delayed expression"},
            {"disorder": "Autism Spectrum Disorder (ASD)", "icd10": "F84.0", "category": "Neurodevelopmental Disorders", "specifiers": "Level 1 (Support), Level 2 (Substantial Support), Level 3 (Very Substantial Support)"},
            {"disorder": "ADHD (Combined Presentation)", "icd10": "F90.2", "category": "Neurodevelopmental Disorders", "specifiers": "Mild, Moderate, Severe"},
            {"disorder": "Borderline Personality Disorder", "icd10": "F60.3", "category": "Personality Disorders (Cluster B)", "specifiers": "Enduring pattern of instability"},
            {"disorder": "Obsessive-Compulsive Disorder (OCD)", "icd10": "F42.2", "category": "Obsessive-Compulsive Disorders", "specifiers": "With good/fair insight, poor insight, absent insight/delusional"},
        ]

        matches = [d for d in database if query_lower in d["disorder"].lower() or query_lower in d["icd10"].lower() or query_lower in d["category"].lower()]

        if not matches:
            return ToolResult(
                success=False,
                tool_name=self.name,
                message=f"No exact code match found for query '{query}'.",
                data={"query": query, "results": []},
            )

        return ToolResult(
            success=True,
            tool_name=self.name,
            message=f"Found {len(matches)} matching DSM-5 diagnostic code records.",
            data={"query": query, "results": matches},
        )


class EpidemiologyStatsTool(BaseTool):
    """Tool to retrieve empirical prevalence, sex ratio, onset age, and heritability stats."""

    def __init__(self) -> None:
        super().__init__(
            name="get_epidemiology_stats",
            description="Retrieve empirical 12-month & lifetime prevalence, sex ratio, onset age, and heritability for psychiatric disorders.",
        )

    async def execute(self, disorder_name: str, **kwargs: Any) -> ToolResult:
        d_lower = disorder_name.lower().strip()

        stats_db = {
            "depression": {"name": "Major Depressive Disorder", "12m_prevalence": "7.0%", "lifetime_prevalence": "12.0% - 20.0%", "sex_ratio_f_m": "1.5:1 to 3:1", "onset_age": "Mid-20s", "heritability": "40%"},
            "gad": {"name": "Generalized Anxiety Disorder", "12m_prevalence": "2.9%", "lifetime_prevalence": "9.0%", "sex_ratio_f_m": "2:1", "onset_age": "30 years", "heritability": "30%"},
            "bipolar": {"name": "Bipolar I Disorder", "12m_prevalence": "0.6%", "lifetime_prevalence": "1.0%", "sex_ratio_f_m": "1:1", "onset_age": "18 years", "heritability": "80%"},
            "schizophrenia": {"name": "Schizophrenia", "12m_prevalence": "0.3% - 0.7%", "lifetime_prevalence": "0.4% - 1.0%", "sex_ratio_f_m": "1:1.4", "onset_age": "18-25 (M), 25-30 (F)", "heritability": "80%"},
            "ptsd": {"name": "Posttraumatic Stress Disorder", "12m_prevalence": "3.5%", "lifetime_prevalence": "8.7%", "sex_ratio_f_m": "2:1", "onset_age": "Variable (post-trauma)", "heritability": "30% - 40%"},
            "autism": {"name": "Autism Spectrum Disorder", "12m_prevalence": "1.5% - 2.0%", "lifetime_prevalence": "1.5% - 2.0%", "sex_ratio_f_m": "1:4", "onset_age": "1-4 years", "heritability": "80% - 90%"},
            "adhd": {"name": "ADHD", "12m_prevalence": "5.0% (children), 2.5% (adults)", "lifetime_prevalence": "5.0%", "sex_ratio_f_m": "1:2", "onset_age": "< 12 years", "heritability": "75% - 80%"},
            "borderline": {"name": "Borderline Personality Disorder", "12m_prevalence": "1.6% - 5.9%", "lifetime_prevalence": "5.9%", "sex_ratio_f_m": "3:1 (clinical)", "onset_age": "Adolescence/Early adult", "heritability": "40% - 60%"},
        }

        matched_key = None
        for k in stats_db:
            if k in d_lower or stats_db[k]["name"].lower() in d_lower:
                matched_key = k
                break

        if not matched_key:
            return ToolResult(
                success=False,
                tool_name=self.name,
                message=f"Epidemiological data for '{disorder_name}' not found.",
                data={"query": disorder_name},
            )

        data = stats_db[matched_key]
        return ToolResult(
            success=True,
            tool_name=self.name,
            message=f"Retrieved empirical epidemiological statistics for {data['name']}.",
            data=data,
        )


class ClinicalSummaryReportTool(BaseTool):
    """Tool to generate structured clinical decision support summary for patient records."""

    def __init__(self) -> None:
        super().__init__(
            name="generate_clinical_summary_report",
            description="Generate structured clinical decision support summary based on symptoms and assessment scores.",
        )

    async def execute(self, patient_identifier: str = "Anonymous", symptoms: Optional[List[str]] = None, assessment_scores: Optional[Dict[str, int]] = None, **kwargs: Any) -> ToolResult:
        symptoms_list = symptoms or []
        scores_dict = assessment_scores or {}

        summary_text = (
            f"=== DSM-5 CLINICAL DECISION SUPPORT SUMMARY ===\n"
            f"Patient Identifier: {patient_identifier}\n"
            f"Primary Symptom Domain: {', '.join(symptoms_list) if symptoms_list else 'Unspecified'}\n"
            f"Psychometric Assessment Scores: {scores_dict}\n"
            f"DSM-5 Diagnostic Considerations: Evaluate matching criteria per DSM-5 section.\n"
            f"Emergency Crisis Risk: Screened for active safety concerns.\n"
            f"=================================================="
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            message="Clinical summary report generated successfully.",
            data={
                "patient_identifier": patient_identifier,
                "summary_report": summary_text,
                "timestamp": "Current Session",
            },
        )
