.PHONY: brain

brain:
	uvicorn brain.chat:app --host 0.0.0.0 --port 8088 --reload

