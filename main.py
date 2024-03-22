import re
from datetime import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructField, StructType, StringType, DateType, DoubleType
from pyspark.sql.functions import udf, regexp_replace
from config.config import configuration


def extract_file_name(file_content):
    file_content = file_content.strip()
    position = file_content.split('\n')[0]
    return position

def extract_position(file_content):
    file_content = file_content.strip()
    position = file_content.split('\n')[0]
    return position

def extract_salary(file_content):
   try:
       salary_match = re.findall(r'\$?(\d{1,3}(?:,\d{3})+)\s*(?:-|to)\s*\$?(\d{1,3}(?:,\d{3})+)', file_content)
       if salary_match:
            salary_start = float(salary_match[0][0].replace(',', ''))
            salary_end = float(salary_match[0][1].replace(',', ''))
            return salary_start, salary_end
       else:
           return None
   except Exception as e:
       raise ValueError(f'Error extracting salary range: {e}')

def extract_class_code(file_content):
    try:
        class_code_match = re.search(r'(Class Code:)\s+(\d+)', file_content)
        if class_code_match:
            class_code = class_code_match.group(2)
            return class_code
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting class code: {e}')

def extract_start_date(file_content):
    try:
        start_date_match = re.search(r'(Open [Dd]ate:)\s+(\d\d-\d\d-\d\d)', file_content)
        if start_date_match:
            start_date = datetime.strptime(start_date_match.group(2), '%m-%d-%y')
            return start_date
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting staring date: {e}')

def extract_end_date(file_content):
    try:
        pattern = r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s(\d{1,2},\s\d{4})'
        end_date_match = re.search(pattern, file_content)

        if end_date_match:
            end_date = datetime.strptime(end_date_match.group(), "%B %d, %Y")
            return end_date
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting application deadline: {e}')

def extract_requirements(file_content):
    try:
        requirements_match = re.search(r'(REQUIREMENTS?/\s?MINIMUM QUALIFICATIONS?)(.*)(PROCESS NOTES?)',
                                       file_content, re.DOTALL)
        if requirements_match:
            requirements = requirements_match.group(2).strip()
            return requirements
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting requirements: {str(e)}')

def extract_notes(file_content):
    try:
        notes_match = re.search(r'(NOTES?):(.*?)(?=DUTIES)', file_content, re.DOTALL | re.IGNORECASE)
        notes = notes_match.group(2).strip() if notes_match else None
        return notes
    except Exception as e:
        raise ValueError(f'Error extracting notes: {str(e)}')

def extract_duties(file_content):
    try:
        duties_match = re.search(r'DUTIES(.*?)REQUIREMENTS?/MINIMUM QUALIFICATIONS?', file_content, re.DOTALL)
        if duties_match:
            duties = duties_match.group(1).strip()
            return duties
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting duties: {str(e)}')

def extract_selection(file_content):
    try:
        selection_match = re.findall(r'([A-Z][a-z]+)(\s\.\s)+', file_content)
        if selection_match:
            selection = [s[0] for s in selection_match]
            return selection
        else:
            return None
    except Exception as e:
        raise ValueError(f'Error extracting selection: {str(e)}')
def extract_experience_length(file_content):
    try:
        experience_length_match = re.search(
            r'(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|one|two|three|four|five)\s(years?)\s(of\sfull(-|\s)time)',
            file_content)
        experience_length = experience_length_match.group(1) if experience_length_match else None
        return experience_length
    except Exception as e:
        raise ValueError(f'Error extracting experience length: {str(e)}')


def extract_education_length(file_content):
    try:
        education_length_match = re.search(
            r'(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|one|two|three|four|five)(\s|-)(years?)\s(college|university)',
            file_content)
        education_length = education_length_match.group(1) if education_length_match else None
        return education_length
    except Exception as e:
        raise ValueError(f'Error extracting education length: {str(e)}')

def extract_application_location(file_content):
    try:
        application_loc_match = re.search(r'(Applications? will only be accepted on-?line)', file_content,
                                          re.IGNORECASE)
        applocation_loc = 'Online' if application_loc_match else 'Mail or In Person'
        return applocation_loc
    except Exception as e:
        raise ValueError(f'Error extracting application location: {str(e)}')

def define_udfs():
    return {
        'extract_file_name_udf': udf(extract_file_name, StringType()),
        'extract_position_udf': udf(extract_position, StringType()),
        'extract_salary_udf': udf(extract_salary, StructType([
            StructField('salary_start', DoubleType(), True),
            StructField('salary_end', DoubleType(), True)
        ])),
        'extract_start_date_udf': udf(extract_start_date, DateType()),
        'extract_end_date_udf': udf(extract_end_date, DateType()),
        'extract_class_code_udf': udf(extract_class_code, StringType()),
        'extract_requirements_udf': udf(extract_requirements, StringType()),
        'extract_notes_udf': udf(extract_notes, StringType()),
        'extract_duties_udf': udf(extract_duties, StringType()),
        'extract_selection_udf': udf(extract_selection, StringType()),
        'extract_experience_length_udf': udf(extract_experience_length, StringType()),
        'extract_education_length_udf': udf(extract_education_length, StringType()),
        'extract_application_location_udf': udf(extract_application_location, StringType())
    }


if __name__ == "__main__":
    spark = (SparkSession.builder.appName('AWS_Spark_Unstructured')
             .config('spark.jars.packages',
                     'org.apache.hadoop:hadoop-aws:3.3.1,'
                     'com.amazonaws:aws-java-sdk:1.12.682')
             .config('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
             .config('spark.hadoop.fs.s3a.access.key', configuration.get('AWS_ACCESS_KEY'))
             .config('spark.hadoop.fs.s3a.secret.key', configuration.get('AWS_SECRET_KEY'))
             .config('spark.hadoop.fs.s3a.aws.credentials.provider',
                     'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider')
             .getOrCreate())

text_input_dir = 'file:///Users/kiellozada/PycharmProjects/Realtime_Streaming_with_AWS_Project/input'

data_schema = StructType([
    StructField('file_name', StringType(), True),
    StructField('position', StringType(), True),
    StructField('classcode', StringType(), True),
    StructField('salary_start', StringType(), True),
    StructField('salary_end', StringType(), True),
    StructField('start_date', DateType(), True),
    StructField('end_date', DateType(), True),
    StructField('req', StringType(), True),
    StructField('notes', StringType(), True),
    StructField('duties', StringType(), True),
    StructField('selection', StringType(), True),
    StructField('experience_length', StringType(), True),
    StructField('job_type', StringType(), True),
    StructField('education_length', StringType(), True),
    StructField('school_type', StringType(), True),
    StructField('application_location', StringType(), True)
])

udfs = define_udfs()

job_bulletins_df = (spark.readStream
                        .format('text')
                        .option('wholetext', 'true')
                        .load(text_input_dir)
                        )

job_bulletins_df = job_bulletins_df.withColumn("file_name",
                                                   regexp_replace(udfs["extract_file_name_udf"]("value"), r'\r', ' '))
job_bulletins_df = job_bulletins_df.withColumn("value", regexp_replace(regexp_replace("value", r'\n', ' '), r'\r', ' '))
job_bulletins_df = job_bulletins_df.withColumn("position",
                                                   regexp_replace(udfs["extract_position_udf"]("value"), r'\r', ' '))
job_bulletins_df = job_bulletins_df.withColumn("salary_start",
                                                   udfs["extract_salary_udf"]("value").getField("salary_start"))
job_bulletins_df = job_bulletins_df.withColumn("salary_end",
                                                   udfs["extract_salary_udf"]("value").getField("salary_end"))
job_bulletins_df = job_bulletins_df.withColumn("start_date", udfs["extract_start_date_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("end_date", udfs["extract_end_date_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("classcode", udfs["extract_class_code_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("req", udfs["extract_requirements_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("notes", udfs["extract_notes_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("duties", udfs["extract_duties_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("selection", udfs["extract_selection_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("experience_length", udfs["extract_experience_length_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("education_length", udfs["extract_education_length_udf"]("value"))
job_bulletins_df = job_bulletins_df.withColumn("application_location", udfs["extract_application_location_udf"]("value"))

job_bulletins_df = job_bulletins_df.select("file_name", "start_date", "end_date", "salary_start", 'salary_end', 'classcode',
                                   'req', 'notes', 'duties', 'selection', 'experience_length',
                                   'education_length', 'application_location')

def streamWriter(input: DataFrame, checkpointFolder, output):
    return (input.writeStream.
            format('parquet')
            .option('checkpointLocation', checkpointFolder)
            .option('path', output)
            .outputMode('append')
            .trigger(processingTime='5 seconds')
            .start())

query = (job_bulletins_df.writeStream
         .outputMode('append')
         .format('console')
         .option('truncate', False)
         .start())

query = streamWriter(job_bulletins_df, 's3a://unstructured-data-realtime-streaming-spark-aws/checkpoints/',
                     's3a://unstructured-data-realtime-streaming-spark-aws/data/spark_unstructured')

query.awaitTermination()

spark.stop()