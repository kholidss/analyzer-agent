VENV_NAME = venv

# Install dependencies
install:
	python3 -m venv $(VENV_NAME)
	. $(VENV_NAME)/bin/activate && pip install -r requirements.txt

# Running HTTP with uvicorn
run:
	. $(VENV_NAME)/bin/activate && python3 -m uvicorn app.main:app --reload

# Remove VENV directory
clean:
	rm -rf $(VENV_NAME)
