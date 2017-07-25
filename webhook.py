from itty import *
import urllib2
import json
import requests
import os

def sendSparkGET(url):
    """
    This method is used for:
        -retrieving message text, when the webhook is triggered with a message
        -Getting the username of the person who posted the message if a command is recognized
    """
    request = urllib2.Request(url,
                            headers={"Accept" : "application/json",
                                     "Content-Type":"application/json"})
    request.add_header("Authorization", "Bearer "+bearer)
    contents = urllib2.urlopen(request).read()
    return contents
    
def sendSparkPOST(url, data):
    """
    This method is used for:
        -posting a message to the Spark room to confirm that a command was received and processed
    """
    request = urllib2.Request(url, json.dumps(data),
                            headers={"Accept" : "application/json",
                                     "Content-Type":"application/json"})
    request.add_header("Authorization", "Bearer "+bearer)
    contents = urllib2.urlopen(request).read()
    
    return contents
    
def get_variation(json):  #Pulls Variations of a prescription from JSON output
    variations = json[1]
    return variations

def send_request(scanurl):   #This function makes a request to the X-Force Exchange API using a specific URL and headers.
    fullurl = scanurl
    response = requests.get(fullurl, params='',timeout=20)
    all_json = response.json()
    return all_json

def get_specific_variation(number):   #Get's the specific variation of a prescription that is described by the user
    rxcui_line = ""
    with open('.variations.txt') as f:
        lines = f.readlines()
        line_count = 0
        for line in lines:
            if(number-1 == 0):
                rxcui_line = get_rxcui(line)
                break
            if(line_count == number-1):
                rxcui_line = get_rxcui(line)
                print line
                break
            else:
                line_count += 1 
    return rxcui_line
               
def get_rxcui(line):         #Returns the list of RXCUIs that comes with a specific variation of a prescription
    return line[1]
@post('/')
def index(request):
    """
    When messages come in from the webhook, they are processed here.  The message text needs to be retrieved from Spark,
    using the sendSparkGet() function.  The message text is parsed.  If an expected command is found in the message,
    further actions are taken. i.e.
    /batman    - replies to the room with text
    /batcave   - echoes the incoming text to the room
    /batsignal - replies to the room with an image
    """
    with open('.precription_count') as f:
        lines = f.readlines()
        for line in lines:
            prescription_count = line[0]      
            f.close()
    with open('.variation_flag.txt') as f:
        lines = f.readlines()
        for line in lines:
            variation_flag = line[0]
            f.close()

    with open(".num_prescription_flag.txt") as f:
        lines = f.readlines()
        for line in lines:
            num_prescription_flag = line[0]
        print num_prescription_flag
        f.close()
    with open(".got_count_flag.txt") as f:
        lines = f.readlines()
        for line in lines:
            got_count = line[0]
        f.close()
    print "COUNT: " + str(got_count)
    webhook = json.loads(request.body)
    result = sendSparkGET('https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
    result = json.loads(result)
    print result
    msg = None
    if webhook['data']['personEmail'] != bot_email:
        in_message = result.get('text', '').lower()
        in_message = in_message.replace(bot_name, '')
        if 'check' and 'prescription' in in_message:
            print "WOw"
            msg = "How many prescriptions are you taking?"
            with open(".num_prescription_flag.txt",'w') as fin:
                fin.write("1")
                fin.close()
            sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "text": msg})
        if int(num_prescription_flag) == 1 and int(got_count) == 0:
            print "HERE"
            prescription_count = int(in_message)
            with open('.precription_count','w') as f:
                f.write(str(prescription_count))
                f.close()
            with open('.got_count_flag.txt','w') as f:
                f.write('1')
                f.close()
            msg = "What is the name of your first prescription?"
            sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "text": msg})
        if int(num_prescription_flag) == 1 and int(got_count) == 1 and int(variation_flag) == 0: 
            print "WOWOEY"
            name_of_drug = in_message.lower()
            url = 'https://clin-table-search.lhc.nlm.nih.gov/api/rxterms/v3/search?terms=' + name_of_drug + '&ef=STRENGTHS_AND_FORMS,RXCUIS'
            json_output = send_request(url)
            variations = get_variation(json_output) 
            x=1
            variations = form_lists_of_variations(json_output)
            msg = "Which variation below is yours?\n"
            with open('.variations.txt','w+') as f: 
                for variation in variations:
                    f.write(str(x) + variation + '\n')
                f.close()    
            for variation in variations:
                
                msg += str(x) + variation + '\n'
                x += 1
            with open('.variation_flag.txt','w') as f:
                f.write('1')
                f.close()
            sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "text": msg})
        if int(variation_flag) == 1:
            rxcui = get_specific_variation(int(in_message))
            msg = "The RXCUI of your prescription is " + str(rxcui)
            sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "text": msg})    
        if 'batman' in in_message or "whoareyou" in in_message:
            msg = "I'm Batman!"
        elif 'batcave' in in_message:
            message = result.get('text').split('batcave')[1].strip(" ")
            if len(message) > 0:
                msg = "The Batcave echoes, '{0}'".format(message)
            else:
                msg = "The Batcave is silent..."
        elif 'batsignal' in in_message:
            print "NANA NANA NANA NANA"
            sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "files": bat_signal})
    return "true"
    
####CHANGE THESE VALUES#####
bot_email = "connectmetodoctor@sparkbot.io"
bot_name = "Cisco_Spark_Challenge"
bearer = "MzM5ZjU1NzMtMjY1NC00ODdmLThkZjItNjRhYjYyYzY4YzI4YWYyNjdmNzUtMDcy"
bat_signal  = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"
run_itty(server='wsgiref', host='0.0.0.0', port=100)
if KeyboardInterrupt:
    print "INTERRUPT"
    os.system('python reset_all_flags.py')
   
