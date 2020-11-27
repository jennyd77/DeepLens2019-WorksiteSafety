# DeepLens2019-WorksiteSafety
A ready to deploy model and Lambda script to run edge processing HardHat detection on an AWS DeepLens 2019 edition


# Step 1: Register your 2019 DeepLens to your AWS account.
For assistance, use https://www.awsdeeplens.recipes/200_beginner/

## Registration
* AWS Console - us-east-1 region - DeepLens - Register Device
* Connect DeepLens to power
* Connect DeepLens (registration port) to local computer via USB-A to USB-A cable
* Power on DeepLens
* Disconnect local computer from VPN (if relevant)
* Wait for blue power light on DeepLens (other two lights will be off)
* Select “Detect AWS DeepLens device”
* Wait up to two minutes until computer shows banner stating that "Device detected successfully"
* At this point, your computer will have created a local network connection to the DeepLens and you can expect to have lost internet connection. 
* You will see the following message in your browser: "Your computer has lost internet connection"
* Click 'Next'
* Enter the last 4 digits of the DeepLens serial number (located on the bottom of the device)
* Enter WiFi details (so that DeepLens can connect to WiFi)
* Click ‘Connect’
* Click 'Next'
* Give the device a name and agree to the permissions
* Ignore any warning about "Network Failure" during this process. This is expected
* Click ‘Register device’
* Wait a few minutes to see the following banner: "Your device has been registered successfully"

### Information to record
#### IOT Topic name
When your DeepLens runs computer vision models, your project code has the option to write output messages to an IOT topic.
From the "Project output" section, record this topic name so that you can look at it later

#### Device IP address
You may wish to directly log in to your DeepLens using SSH.
To do this, grab the DeepLens IP address from the "Device details" section
You can test ssh using the command ssh aws_cam@<IP address of your device>

## Viewing output from the DeepLens
There are two ways to view the output:
1)	Connect the DeepLens directly to a monitor
2)	Stream the video over the WiFi network to your laptop

### Connect the DeepLens directly to a monitor
Note: The registration port on the 2019 DeepLens is not a regular USB port.
If you want to connect both a keyboard and mouse to the DeepLens you will need a USB hub or a 2-in-1 keyboard and mouse

Connect keyboard, monitor and mouse to the DeepLens and login to Ubuntu
Open “Terminal”

To see the standard video feed (no ML inference)
```mplayer -demuxer lavf /opt/awscam/out/ch1_out.h264```
Wait 30 seconds and ignore any warnings about not being able to use your remote control

To see the project feed (with ML inference)
```mplayer -demuxer lavf -lavfdopts format=mjpeg:probesize=32 /tmp/results.mjpeg```

# Step 2: Upload the model artifact to your S3 bucket
* The original model.tar.gz file was split into 3 smaller files in order to stay under the github maximum file size
* On your laptop, rejoin the 3 model files using the following commands:
   - cat modeltargzaa > model.tar.gz
   - cat modeltargzab >> model.tar.gz
   - cat modeltargzac >> model.tar.gz 

* AWS Console - us-east-1 region - S3 - Create Bucket
* Create an S3 bucket that has a name starting with “deeplens-“
* Create a folder “worksite-safety/model”
* Upload the file ```model.tar.gz``` to the new folder in your S3 bucket

# Step 3: Create the Lambda function which will run on your DeepLens
* Download the AWS DeepLens inference function template to your computer. Do not unzip the downloaded file
   ```https://docs.aws.amazon.com/deeplens/latest/dg/samples/deeplens_inference_function_template.zip```
* AWS Console - us-east-1 region - Lambda
* Create Function - Author from Scratch
* Function Name: deeplens-worksite-safety-custom
* Runtime: Python 3.7
* Permissions - Execution role - service-role/AWSDeepLensLambdaRole
* Create function
* Function code - Upload a .zip file - deeplens_inference_function_template.zip
* Save
* Lambda code editor - open lambda_function.py
* Overwrite contents of lambda_function.py with provided code from this github repo
* File-Save
* Deploy
* Actions - Publish new version

# Step 4: Create DeepLens project
* AWS Console - us-east-1 region - DeepLens - Create Project
* Start with blank
* Project Name: WorksiteSafety
* Description: “Find heads with HardHats (compliant) and without HardHats (not compliant)”

* Add model
* Import model
* Externally trained model
* Model artifact path: <Enter the full path to the model file: e.g. s3://<bucket_name>/worksitesafety/model/model.tar.gz >
* Model name: WorksiteSafety-ObjectDetector
* Model framework: MXNet
* Description: Trained using SageMaker built in object detector based on MXNet with about 700 images containing between 1 and 6 people
* Import model

* Add function
* Select your lambda function (with the correct version number)
* Click “Add function”
* Click ‘Create’

# Step 5: Deploy project to your DeepLens device
* AWS Console - us-east-1 region - DeepLens
* Projects
* Select radio button next to project “WorksiteSafety”
* Click ‘Deploy to device’
* Select radio button next to your DeepLens
* Click ‘Review’
* Click ‘Deploy’








