# After editing resume.yaml, build resume.pdf:
#   make pdf

.PHONY: pdf

pdf:
	docker compose run --rm pdf
