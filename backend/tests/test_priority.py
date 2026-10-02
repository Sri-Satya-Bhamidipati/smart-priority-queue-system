from app.core.priority import calculate_priority, waiting_score


def test_priority_uses_configured_weighted_scores():
	assert calculate_priority("BANK", "HIGH", "DOCUMENT_VERIFICATION", 0) == 49.0


def test_waiting_score_scales_and_caps():
	assert waiting_score(0) == 0
	assert round(waiting_score(5), 2) == 16.67
	assert round(waiting_score(10), 2) == 33.33
	assert waiting_score(15) == 50
	assert round(waiting_score(20), 2) == 66.67
	assert waiting_score(30) == 100
	assert waiting_score(90) == 100
