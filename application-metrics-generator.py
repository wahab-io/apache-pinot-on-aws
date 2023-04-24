## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0
## Licensed under the MIT License. See the LICENSE accompanying this file
## for the specific language governing permissions and limitations under
## the License.
import sys
import os
import json
import random
import datetime
import boto3

start_time = datetime.datetime.now()
no_of_days = 30

workload_contexts_distribution = [2, 15, 20, 18, 30, 15]
workload_contexts = {
        "OnBoardingApplication": ['TenantCreation', 'UserCreation'],
        "AuthApplication": ['Login', 'Logout', 'PasswordReset'],
        "PhotoApplication": ['PhotoUpload', 'PhotoEdit', 'PhotoDelete'],
        "MessagingApplication": ['SendMessage', 'SendBulkMessages', 'DeleteMessages', 'ArchiveMessages'],
        "ProductApplication": ['ViewProduct', 'ViewProductDetails', 'AddNewProduct', 'DeleteProduct', 'UpdateProduct'],
        "BatchWorkload": ['ActiveProductsReport', 'DailyTransactionReport', 'DailyInventoryReport', 'DailySalesReport']
}

tenant_distribution = [5, 10, 20, 15, 2, 3, 10, 5, 25, 5]
regular_tenants = [
        {"id": "tenant-id-1", "name":"tenant-name-a", "tier":"standard"},
        {"id": "tenant-id-2", "name":"tenant-name-b", "tier":"premium"},
        {"id": "tenant-id-3", "name":"tenant-name-c", "tier":"basic"},
        {"id": "tenant-id-4", "name":"tenant-name-d", "tier":"basic"},
        {"id": "tenant-id-5", "name":"tenant-name-e", "tier":"standard"},
        {"id": "tenant-id-6", "name":"tenant-name-f", "tier":"standard"},
        {"id": "tenant-id-7", "name":"tenant-name-g", "tier":"free"},
        {"id": "tenant-id-8", "name":"tenant-name-h", "tier":"free"},
        {"id": "tenant-id-9", "name":"tenant-name-i", "tier":"basic"},
        {"id": "tenant-id-0", "name":"tenant-name-j", "tier":"free"}
]

user_distribution = [10, 40, 20, 30]
users = ('user-1', 'user-2', 'user-3', 'user-4')

resource_metrics = {
        "s3":  ["Storage", "DataTransfer"],
        "load-balancer":  ["ExecutionTime"],
        "lambda":  ["ExecutionTime"],
        "dynamo-db":  ["Storage", "ExecutionTime", "DataTransfer"],
        "rds": ["Storage", "ExecutionTime", "DataTransfer"]
}

def generate_random_metric_value(metric_name):
        metric = {}
        if metric_name == "Storage":
                metric = {'name' : 'Storage', 'unit' : 'MB', 'value' : random.randrange(50, 5000, 100)}
        elif metric_name == "ExecutionTime":
                metric = {'name' : 'ExecutionTime', 'unit' : 'MilliSeconds', 'value' : random.randrange(100, 5000, 200)}
        elif metric_name == "DataTransfer":
                metric = {'name' : 'DataTransfer', 'unit' : 'MB', 'value' : random.randrange(10, 3000, 200)}

        return metric

def event_time():
        random_days = random.randint(1, no_of_days)
        prev_days  = start_time + datetime.timedelta(days=random_days)
        random_minute = random.randint(0, 59)
        random_hour = random.randint(0, 23)
        time =  prev_days + datetime.timedelta(hours=random_hour) + datetime.timedelta(minutes=random_minute)
        return int(time.timestamp())

def input_with_default(msg, default):
        value = input(msg + " [" + default + "] : ")
        if value == "":
                value = default
        return value

def generate_metric_for(workload, tenants):
        selected_context = random.choice(workload_contexts[workload])
        selected_resource = random.choice(list(resource_metrics.keys()))
        selected_metric_name = random.choice(resource_metrics[selected_resource])
        random_metric_value = generate_random_metric_value(selected_metric_name)

        application_metric = {
                'type' : 'Application',
                'workload': workload,
                'context': selected_context,
                'tenant' : random.choices(tenants, tenant_distribution)[0],
                'metric': random_metric_value,
                'timestamp': event_time(),

                'metadata' : {'user' : random.choices(users, user_distribution)[0], 'resource': selected_resource}
        }
        #print(application_metric)
        return application_metric

def generate_metrics_for(tenants, no_of_metrics, data_stream, batch_size):
        metrics_batch = []

        current_session =  boto3.session.Session()
        # firehose_client = boto3.client('firehose') Sample
        stream_client = current_session.client('kinesis')


        for m in range(no_of_metrics):
                selected_workload = random.choices(list(workload_contexts.keys()), workload_contexts_distribution)[0]

                if len(metrics_batch) < batch_size:
                        print("Generating Metric for: " + selected_workload)
                        metric = generate_metric_for(selected_workload, tenants)
                        json_content= json.dumps(metric)+ '\n'
                        print(json_content)

                        stream_client.put_record(
                                StreamName=data_stream,
                                Data=json_content, PartitionKey= str(metric['tenant'])
                        )


def display(msg):
        print("___________________________________")
        print(msg + "...")
        print("___________________________________")



if __name__ == "__main__":
        try:
                number_of_metrics_to_generate = 10000000
                start_at =  "2020-01-01"
                start_time = datetime.datetime.strptime(start_at, "%Y-%m-%d")
                no_of_days = 30
                batch_size = 25
                stream_name = sys.argv[1]


                display("Generating Event Metrics: " + str(number_of_metrics_to_generate))
                generate_metrics_for(regular_tenants, number_of_metrics_to_generate, stream_name, batch_size)

        except Exception as e:
                print("error occured")
                print(e)
                raise
