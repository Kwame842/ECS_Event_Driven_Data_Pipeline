# Base image with Spark + Hadoop + Python
FROM jupyter/pyspark-notebook:spark-3.4.1

USER root

# Install any extra Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Add required Hadoop AWS JARs
ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar /usr/local/spark/jars/
ADD https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.698/aws-java-sdk-bundle-1.12.698.jar /usr/local/spark/jars/

# Set working directory
WORKDIR /app

# Copy script(s) and .env
COPY transformer.py .
COPY .env .

# Run
CMD ["spark-submit", "transformer.py"]
