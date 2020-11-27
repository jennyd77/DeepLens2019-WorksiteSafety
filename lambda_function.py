import json
import awscam
import mo
import cv2
import greengrasssdk
import os
from local_display import LocalDisplay

def lambda_handler(event, context):
    """Empty entry point to the Lambda function invoked from the edge."""
    return

def infinite_infer_run():
    """ Entry point of the lambda function"""
    try:
        # This object detection model is implemented as single shot detector (ssd), since
        # the number of labels is small we create a dictionary that will help us convert
        # the machine labels to human readable labels.
        model_type = 'ssd'

        ######### Changed ###########
        output_map = {0: 'compliant', 1: 'not compliant'}
        green=(0, 255, 0)
        red=(0, 0, 255)
        colour_map = {0: green, 1: red}
        #####################################

        # The height and width of the training set images
        input_height = 512
        input_width = 512

        # Create an IoT client for sending to messages to the cloud.
        client = greengrasssdk.client('iot-data')
        iot_topic = '$aws/things/{}/infer'.format(os.environ['AWS_IOT_THING_NAME'])

        # Create a local display instance that will dump the image bytes to a FIFO
        # file that the image can be rendered locally.
        local_display = LocalDisplay('480p')
        local_display.start()
        ################################################################################################################
        ###                                                                                                          ###
        ###  Load the model                                                                                          ###
        ###  Note: This is a SageMaker trained SSD model                                                             ###
        ###        Therefore it is a requirement that                                                                ###
        ###        the model must have previously been                                                               ###
        ###        concerted to deployable model                                                                     ###
        ###        Details: https://docs.aws.amazon.com/deeplens/latest/dg/deeplens-templated-projects-overview.html ###
        ###                                                                                                          ###
        ################################################################################################################
        model_path = '/opt/awscam/artifacts/model_algo_1.xml'
        model_name = 'model_algo_1'

        # Load the model onto the GPU.
        client.publish(topic=iot_topic, payload='Loading object detection model')
        model = awscam.Model(model_path, {'GPU': 1})
        client.publish(topic=iot_topic, payload='Object detection model loaded')
        # Set the confidence threshold for detection
        detection_threshold = 0.4
        # Do inference until the lambda is killed.
        while True:
            # Get a frame from the video stream
            ret, frame = awscam.getLastFrame()
            if not ret:
                raise Exception('Failed to get frame from the stream')
            # Resize frame to the same size as the training set.
            frame_resize = cv2.resize(frame, (input_height, input_width))
            # Run the images through the inference engine and parse the results using
            # the parser API, note it is possible to get the output of doInference
            # and do the parsing manually, but since it is a ssd model,
            # a simple API is provided.
            parsed_inference_results = model.parseResult(model_type,
                                                         model.doInference(frame_resize))
            # Compute the scale in order to draw bounding boxes on the full resolution
            # image.
            yscale = float(frame.shape[0])/float(input_height)
            xscale = float(frame.shape[1])/float(input_width)
            # Create a dictionary to be filled with labels and probabilities for MQTT
            cloud_output = {}
            # Get the detected objects and probabilities
            for obj in parsed_inference_results[model_type]:
                if obj['prob'] > detection_threshold:
                    # Add bounding boxes to full resolution frame
                    xmin_i = int(xscale * obj['xmin']) + int((obj['xmin'] - input_width/2))
                    xmax_i = int(xscale * obj['xmax']) + int((obj['xmax'] - input_width/2))
                    width_box = float(xmax_i - xmin_i)
                    midpoint_box = float(xmin_i) + 0.5 * width_box
                    reference_point = midpoint_box/float(frame.shape[1])
                    x_step = width_box * (0.5 - reference_point)
                    xmin = int(xmin_i + x_step)
                    ymin = int(yscale * obj['ymin'])
                    xmax = int(xmax_i + x_step)
                    ymax = int(yscale * obj['ymax'])
                    ###################################
                    # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                    # for more information about the cv2.rectangle method.

                    # Lookup the label for the object detected as well as the colour to be used for the label
                    output = output_map[obj['label']]
                    colour = colour_map[obj['label']]

                    # Draw the bounding box on screen with the mapped colour
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), colour, 10)

                    # Write the label just above the bounding box
                    # Amount to offset the label/probability text above the bounding box.
                    text_offset = 15
                    # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                    # for more information about the cv2.putText method.
                    cv2.putText(frame, "{}: {:.2f}%".format(output_map[obj['label']],
                                                               obj['prob'] * 100),
                                (xmin, ymin-text_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.5, colour, 6)
                    # Store label and probability in our dictionary
                    cloud_output[output_map[obj['label']]] = obj['prob']
            # Set the next frame in the local display stream.
            local_display.set_frame_data(frame)
            # Send results to the cloud
            client.publish(topic=iot_topic, payload=json.dumps(cloud_output))
    except Exception as ex:
        client.publish(topic=iot_topic, payload='Error in object detection lambda: {}'.format(ex))

infinite_infer_run()
