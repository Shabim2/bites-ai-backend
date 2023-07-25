import os
import re
import sys
import boto3
import tempfile

from xml.etree import ElementTree
from collections import Counter, OrderedDict

__version__ = '1.3'

RECORD_FIELDS = OrderedDict((
    ('sourceName', 's'),
    ('sourceVersion', 's'),
    ('device', 's'),
    ('type', 's'),
    ('unit', 's'),
    ('creationDate', 'd'),
    ('startDate', 'd'),
    ('endDate', 'd'),
    ('value', 'n'),
))

ACTIVITY_SUMMARY_FIELDS = OrderedDict((
    ('dateComponents', 'd'),
    ('activeEnergyBurned', 'n'),
    ('activeEnergyBurnedGoal', 'n'),
    ('activeEnergyBurnedUnit', 's'),
    ('appleExerciseTime', 's'),
    ('appleExerciseTimeGoal', 's'),
    ('appleStandHours', 'n'),
    ('appleStandHoursGoal', 'n'),
))

WORKOUT_FIELDS = OrderedDict((
    ('sourceName', 's'),
    ('sourceVersion', 's'),
    ('device', 's'),
    ('creationDate', 'd'),
    ('startDate', 'd'),
    ('endDate', 'd'),
    ('workoutActivityType', 's'),
    ('duration', 'n'),
    ('durationUnit', 's'),
    ('totalDistance', 'n'),
    ('totalDistanceUnit', 's'),
    ('totalEnergyBurned', 'n'),
    ('totalEnergyBurnedUnit', 's'),
))

FIELDS = {
    'Record': RECORD_FIELDS,
    'ActivitySummary': ACTIVITY_SUMMARY_FIELDS,
    'Workout': WORKOUT_FIELDS,
}


PREFIX_RE = re.compile('^HK.*TypeIdentifier(.+)$')
ABBREVIATE = True
VERBOSE = True

def format_freqs(counter):
    """
    Format a counter object for display.
    """
    return '\n'.join('%s: %d' % (tag, counter[tag])
                     for tag in sorted(counter.keys()))


def format_value(value, datatype):
    """
    Format a value for a CSV file, escaping double quotes and backslashes.
    None maps to empty.
    datatype should be
        's' for string (escaped)
        'n' for number
        'd' for datetime
    """
    if value is None:
        return ''
    elif datatype == 's':  # string
        return '"%s"' % value.replace('\\', '\\\\').replace('"', '\\"')
    elif datatype in ('n', 'd'):  # number or date
        return value
    else:
        raise KeyError('Unexpected format value: %s' % datatype)


def abbreviate(s, enabled=ABBREVIATE):
    """
    Abbreviate particularly verbose strings based on a regular expression
    """
    m = re.match(PREFIX_RE, s)
    return m.group(1) if enabled and m else s


class HealthDataExtractor(object):
    """
    Extract health data from Apple Health App's XML export, export.xml.
    Inputs:
        path:      Relative or absolute path to export.xml
        verbose:   Set to False for less verbose output
    Outputs:
        Writes a CSV file for each record type found, in the same
        directory as the input export.xml. Reports each file written
        unless verbose has been set to False.
    """
    def __init__(self, file, verbose=VERBOSE):
        self.verbose = verbose
        self.report('Reading data from')
        self.data = ElementTree.fromstring(file)
        self.report('done')
        self.root = self.data
        self.nodes = list(self.root)
        self.n_nodes = len(self.nodes)
        print('HERE')
        self.abbreviate_types()
        print('HERE')
        self.collect_stats()

    def report(self, msg, end='\n'):
        if self.verbose:
            print(msg, end=end)
            sys.stdout.flush()

    def count_tags_and_fields(self):
        self.tags = Counter()
        self.fields = Counter()
        for record in self.nodes:
            self.tags[record.tag] += 1
            for k in record.keys():
                self.fields[k] += 1

    def count_record_types(self):
        """
        Counts occurrences of each type of (conceptual) "record" in the data.
        In the case of nodes of type 'Record', this counts the number of
        occurrences of each 'type' or record in self.record_types.
        In the case of nodes of type 'ActivitySummary' and 'Workout',
        it just counts those in self.other_types.
        The slightly different handling reflects the fact that 'Record'
        nodes come in a variety of different subtypes that we want to write
        to different data files, whereas (for now) we are going to write
        all Workout entries to a single file, and all ActivitySummary
        entries to another single file.
        """
        self.record_types = Counter()
        self.other_types = Counter()
        for record in self.nodes:
            if record.tag == 'Record':
                self.record_types[record.attrib['type']] += 1
            elif record.tag in ('ActivitySummary', 'Workout'):
                self.other_types[record.tag] += 1
            elif record.tag in ('Export', 'Me'):
                pass
            else:
                self.report('Unexpected node of type %s.' % record.tag)

    def collect_stats(self):
        self.count_record_types()
        self.count_tags_and_fields()

    def abbreviate_types(self):
        """
        Shorten types by removing common boilerplate text.
        """
        for node in self.nodes:
            if node.tag == 'Record':
                if 'type' in node.attrib:
                    node.attrib['type'] = abbreviate(node.attrib['type'])

    def extract(self, record_type):
            # Assuming self.record_types and self.other_types are already populated with record types
            bucket_name = 'bites-ai-dev'
            key = '%s.csv' % abbreviate(record_type)

            header = 'activity,unit,endtime,starttime,time,value\n'  # Header row

            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                # Create a temporary file to store the CSV rows for the current record type
                for node in self.nodes:
                    attributes = node.attrib
                    kind = attributes['type'] if node.tag == 'Record' else node.tag
                    if kind == record_type:
                        values = [format_value(attributes.get(field), datatype) for (field, datatype) in FIELDS[node.tag].items()]
                        csv_row = ','.join(values).encode('utf-8')

                        # Split the row into values and skip the first three values
                        row_values = csv_row.split(b',')[9:]

                        # Join the remaining values back into a CSV row and write to the file
                        cleaned_csv_row = b','.join(row_values) + b'\n'

                        if temp_file.tell() == 0:
                            temp_file.write(header.encode('utf-8'))
                            
                        temp_file.write(cleaned_csv_row)

            # Upload the temporary file to S3
            s3_client.upload_file(temp_file.name, bucket_name, key)

            self.report(f'CSV data for {record_type} upload completed.')



    def report_stats(self):
        print('\nTags:\n%s\n' % format_freqs(self.tags))
        print('Fields:\n%s\n' % format_freqs(self.fields))
        print('Record types:\n%s\n' % format_freqs(self.record_types))

s3_client = boto3.client("s3")
	
def handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    # Create a Boto3 S3 client
    s3_client = boto3.client('s3')
    try:
        # Read the contents of the S3 object
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_contents = response['Body'].read().decode('utf-8')
        # Process the file_contents here (e.g., perform some operations)

        # Optionally, you can return the file contents if needed for further processing or integration

        data = HealthDataExtractor(file_contents)
        data.report_stats()

        # Assuming self.record_types and self.other_types are already populated with record types
        for record_type in (list(data.record_types) + list(data.other_types)):
            data.extract(record_type)

        return {
            'statusCode': 200,
        }

    except Exception as e:
        # Handle any exceptions that may occur during the file read or processing
        print('error', e)
        return {
            'statusCode': 500,
            'body': 'Error reading or processing the file.'
        }