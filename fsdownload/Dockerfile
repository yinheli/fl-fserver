FROM python:3.12-slim
WORKDIR /app
RUN pip install gunicorn
COPY . /app
RUN pip install --no-cache-dir -r requirement.txt
EXPOSE 5555
CMD ["gunicorn", "-b", "0.0.0.0:5555", "--workers", "2", "--preload", "run:app"]
