import pyttsx3
import pyaudio
import wave
import pyaudio
import time
import speech_recognition as sr
import threading


# Create a PyAudio instance
# Print the list of available audio devices
def identify_devices(printDevices=True, sayDevices=False):

    p = pyaudio.PyAudio()
        
    print("Available audio devices:")

    for index in range(p.get_device_count()):
        dev = p.get_device_info_by_index(index)
        if printDevices:
            print(f"{index}: {dev['name']}")
            
        if sayDevices:
            commands = [str(index),'#WAIT 0.25',dev['name']]
            trigger_alexa(commands,wakeword='',device_index = index)

    # Terminate the PyAudio instance
    p.terminate()


def getDeviceIndex(name):

    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['name'] == name:
            p.terminate()
            return i

    printAvailableDevices()
    p.terminate()
    raise Exception("Device Not Found")
    

def play_audio(file_name, device_index=None):
    # Open the file
    wf = wave.open(file_name, 'rb')

    # Create a PyAudio instance
    p = pyaudio.PyAudio()

    # Open a stream on the specified device
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_index)

    # Read data and play it
    
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Close and terminate everything
    stream.close()
    p.terminate()
    

def make_wav(text, filename="temp.wav", rate = 150):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    # Choose a voice (replace '1' with the index of the desired voice)
    engine.setProperty('voice', voices[0].id)

    engine.setProperty('rate',rate)
    engine.save_to_file(text, filename)
    engine.runAndWait()
    

def record_ambient_noise(file_name = 'ambient_noise.wav', record_seconds=1):
    # Setup audio stream parameters
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream for recording
    stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk,output_device_index=3)

    print("Recording ambient noise...", end='')

    frames = []

    # Record for the specified duration
    for i in range(0, int(rate / chunk * record_seconds)):
        print(".", end='')
        data = stream.read(chunk)
        frames.append(data)

    print(" done")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def speak(command,device_index,parallel=False):

    make_wav(command,'command.wav')
    print(f'Saying {command}')
    
    if parallel:
        
        speak_thread = threading.Thread(target=play_audio,args=('command.wav',device_index))
        speak_thread.start()

        
    else:
        play_audio('command.wav', device_index=device_index)
                

def trigger_alexa(commands, wakeword="Alexa",device_index=0):
    
    try:
        if(wakeword):
            
         speak(wakeword,device_index)
          
        for command in commands:    
            
            if command[-1] == '#':
                args = command.split()
                
                if args[0] == 'WAIT':
                    time.sleep(float(args[1]))
                    
                if args[0] == 'LISTEN':
                    print("Hearing:",end='')
                    print(hear_response(float(args[1])))
                    
                    
            elif command[-1] == '?':
                
                speak(command,device_index,True)
                
            else:
                speak(command,device_index)
                    
    except OSError as e:
        print(f'Ignoring OSError {e}')
    except Exception as e:
        print(f'Ignoring {e}')

def hear_response(phrase_time_limit = 30,timeout=3,ambient_noise = 'ambient_noise.wav'):
  
    # Exception handling to handle
    # exceptions at the runtime
    starttime = time.time()
    try:
        r = sr.Recognizer()


        with sr.AudioFile(ambient_noise) as source:
            recognizer = sr.Recognizer()
            # Adjust the recognizer sensitivity to ambient noise
            recognizer.adjust_for_ambient_noise(source)   


        # use the microphone as source for input.
        with sr.Microphone(device_index = 3) as source2:
             
            # wait to let the recognizer
            # adjust the energy threshold based on
            # the surrounding noise level 
            r.adjust_for_ambient_noise(source2, duration=0.2)
             
            #listens for the user's input 
            audio2 = r.listen(source2,timeout=timeout, phrase_time_limit = phrase_time_limit)
             
            # Using google to recognize audio
            MyText = r.recognize_google(audio2)
            MyText = MyText.lower()
 
            #print(MyText)
            return(MyText)
            
            stop = MyText.count("stop")
             
    except sr.RequestError as e:
        return None
         
    except sr.UnknownValueError:
        # It heard a weird noise it couldn't interpret
        # if we have any time left to listen, we'll continue with the remaining time
        # often the alexa 'boop' acknowledgement triggers this.
        
        timerun = time.time() - starttime
        print(".",end='')
        
        return hear_response(phrase_time_limit - timerun)

    except sr.WaitTimeoutError:
        return "timeoutted"
    
            
#Do Stuff
if __name__ == '__main__':

    
    MY_DEVICE = "Speakers (Realtek(R) Audio)" ## Insert your device name here, if you don't know it, uncomment the following line

    #identify_devices(printDevices=True, sayDevices= True)

    record_ambient_noise()

    #Commands
    #command ending with a # indicates a space-separated special command sequence:
        #WAIT x # Waits x seconds
        #LISTEN x # Listens for a reply of up to x seconds, currently just prints it to screen
    
    #"A QUESTION?" with a question mark, speaks, but runs the next command immediately, designed to be followed by a 'listen'
    
    #"Any other text" anything else is just read out.
    
    #Any other string just speaks
    
    commands = ["WAIT 0.0125 #","What is the weather forecast?", 'LISTEN 20 #']
    #commands = ["WAIT 0.0125 #","What is the time?", 'LISTEN 10 #']
    #commands = ["WAIT 0.0125 #","Open the Pod Bay Doors?", 'LISTEN 10 #'] 

    trigger_alexa(commands,wakeword='A Leck Sir',device_index = getDeviceIndex(MY_DEVICE)) ## 'A Leck Sir' seems to work better than Alexa...



    
    

