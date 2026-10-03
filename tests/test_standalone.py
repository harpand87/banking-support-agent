import json

from app.standalone import run_evaluation


def test_standalone_run_writes_reports_and_summary(tmp_path, capsys):
    report = run_evaluation(tmp_path, open_report=False)

    json_report = json.loads((tmp_path / "evaluation-results.json").read_text(encoding="utf-8"))
    html_report = (tmp_path / "evaluation-report.html").read_text(encoding="utf-8")
    output = capsys.readouterr().out

    assert report["case_count"] == 20
    assert json_report["offline_evaluation"]["with_rag"]["decision_accuracy"] == 1.0
    assert json_report["run_metadata"]["model_used"].startswith("OfflineModel")
    assert json_report["run_metadata"]["live_model_used"] is False
    assert json_report["target_matrix"]["met_count"] == 4
    assert json_report["capstone_matrix"]["source"] == "Week+21+Capstone+Project.pdf"
    assert json_report["capstone_matrix"]["phase_summary"] == {"evidenced": 8, "partial": 1, "total": 9}
    assert json_report["capstone_matrix"]["deliverable_summary"] == {"evidenced": 5, "total": 5}
    assert json_report["capstone_matrix"]["minimum_bar_summary"] == {"evidenced": 5, "partial": 1, "total": 6}
    assert "Banking Support Agent offline evaluation complete" in output
    assert "Target matrix achieved: 4/4 checks" in output
    assert "Week+21 matrix: 8/9 phases evidenced, 1 partial" in output
    assert "before/after root-cause analysis is still listed as outstanding" in output
    assert "Decision accuracy: 100.0%" in output
    assert "Case results" in html_report
    assert "Track B - Framework-Free" in html_report
    assert "docs/problem-framing.md#success-criteria" in html_report
    assert "Week+21 capstone matrix" in html_report
    assert "5/6 evidenced; 1 partial" in html_report