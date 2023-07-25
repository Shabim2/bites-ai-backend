import os
import re
import sys
import boto3

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

    def open_for_writing(self):
        # self.handles = {}
        # self.paths = []
        # for kind in (list(self.record_types) + list(self.other_types)):
        #     path = os.path.join(self.directory, '%s.csv' % abbreviate(kind))
        #     f = open(path, 'w')
        #     headerType = (kind if kind in ('Workout', 'ActivitySummary')
        #                        else 'Record')
        #     f.write(','.join(FIELDS[headerType].keys()) + '\n')
        #     self.handles[kind] = f
        #     self.report('Opening %s for writing' % path)
        self.handles = {}
        self.paths = []
        for kind in (list(self.record_types) + list(self.other_types)):
            key = '%s.csv' % abbreviate(kind)
            headerType = (kind if kind in ('Workout', 'ActivitySummary') else 'Record')
            header = ','.join(FIELDS[headerType].keys()) + '\n'
            self.handles[kind] = header  # Store the headers temporarily in memory
            self.report('Opening %s for writing' % key)

        # Upload the headers to S3
        for kind, header in self.handles.items():
            key = '%s.csv' % abbreviate(kind)
            bucket_name = 'bites-ai-dev'
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=header)

    def abbreviate_types(self):
        """
        Shorten types by removing common boilerplate text.
        """
        for node in self.nodes:
            if node.tag == 'Record':
                if 'type' in node.attrib:
                    node.attrib['type'] = abbreviate(node.attrib['type'])

    def write_records(self):
        # kinds = FIELDS.keys()
        # for node in self.nodes:
        #     if node.tag in kinds:
        #         attributes = node.attrib
        #         kind = attributes['type'] if node.tag == 'Record' else node.tag
        #         values = [format_value(attributes.get(field), datatype)
        #                   for (field, datatype) in FIELDS[node.tag].items()]
        #         line = ','.join(values) + '\n'
        #         self.handles[kind].write(line)
        kinds = FIELDS.keys()
        for node in self.nodes:
            if node.tag in kinds:
                attributes = node.attrib
                kind = attributes['type'] if node.tag == 'Record' else node.tag
                values = [format_value(attributes.get(field), datatype) for (field, datatype) in FIELDS[node.tag].items()]
                line = ','.join(values) + '\n'
                self.handles[kind] += line

    def close_files(self):
        # for (kind, f) in self.handles.items():
        #     f.close()
        #     self.report('Written %s data.' % abbreviate(kind))
        self.report('Data extraction completed.')


    def write_csv_to_s3(bucket_name, object_key, csv_data):
        # Prepare the CSV data as a string
        csv_string = '\n'.join([','.join(row) for row in csv_data])

        try:
            # Upload the CSV data to S3
            s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_string)
            return True
        except Exception as e:
            print("Error:", e)
            return False
    
    def extract(self):
        csv_data = {}
        
        # Assuming self.record_types and self.other_types are already populated with record types
        
        for kind in (list(self.record_types) + list(self.other_types)):
            csv_data[kind] = []  # Initialize a list to store CSV data for each record type
        
        for node in self.nodes:
            if node.tag in csv_data:
                attributes = node.attrib
                kind = attributes['type'] if node.tag == 'Record' else node.tag
                values = [format_value(attributes.get(field), datatype) for (field, datatype) in FIELDS[node.tag].items()]
                csv_data[kind].append(values)
        
        # Upload each CSV to S3
        bucket_name = 'bites-ai-dev'
        for kind, data in csv_data.items():
            print(kind)
            print(data)
            key = '%s.csv' % abbreviate(kind)
            csv_string = '\n'.join([','.join(row) for row in data])
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=csv_string)

        self.report('Data extraction completed.')

    # def extract(self):
    #     self.open_for_writing()
    #     self.write_records()
    #     self.close_files()

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

        # Print the file contents (you can replace this with your desired processing logic)

        # Optionally, you can return the file contents if needed for further processing or integration

        data = HealthDataExtractor(file_contents)
        data.report_stats()
        data.extract()
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