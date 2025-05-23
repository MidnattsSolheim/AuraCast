# AuraCast

 Auracast is a multisensory network monitoring tool built to reduce cognitive load in security analysts by transforming network data into **procedural music**, **ambient lighting**, and **visual alerts**.

Sound weird? Good. It is. 

Built for anomaly detection. Powered by the warp.

## Features

- 🎵 **Sonification** of network events using real-time procedural music
- 💡 **Ambient lighting** via Philips Hue to indicate alert severity
- 📜 Suricata **alert ingestion** via JSON
- 🧱 **Modular adapters** for UI, console, and audio/visual feedback
- 🧠 Built to explore human perception in threat detection

## How to Run

1. Navigate to the project folder:   `cd /~AuraCast`
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` - if done right, the prompt will change to show `(venv)`
4. Install the dependencies from requirements.txt: `pip install -r requirements.txt`
5. Install Surge XT
6. Install Carla and launch it 
7. Download the Carla plugin you see in the files and open it in Carla 
8. Connect everything like so:

  This is Canvas -> Show Internal
  
  ![carlainternal](https://res.cloudinary.com/ddbmrer46/image/upload/v1746192114/carla_int_ygwhi5.png)

  This is Canvas -> Show External
  
  ![carlaexternal](https://res.cloudinary.com/ddbmrer46/image/upload/v1746192114/carla_ext_hidrdz.png)
  
9. Download the PCAP file from [here](https://www.malware-traffic-analysis.net/2017/12/29/index2.html) if you want to replicate everything exactly as I did it, otherwise any PCAP file would do, as long as it has something to detect
10. Change the IP address of the Bridge, the interface and the file location in **config.json**
11. Run the app as root: `sudo python main.py`
12. Magic

## Project Notes

1. It's _very much_ a proof-of-concept thing
2. It might be unstable
3. It requires Linux (I use Ubuntu 24.04). I never ran it on Windows, but with all the dependencies it would really be a hassle to even try. Plus, the multithreading mechanisms used in the code are designed to work with *nix systems
4. Considering the PoC nature of it, it doesn't really have a live monitoring functionality yet - there was no way to test it in conditions that I could replicate for each participant, so it was put on the back burner for the duration of the academic part of it. It _does_ have the adapter that captures traffic, but it doesn't do much with it, so in other words: the functionality is there, but it's not really used as per the explanation above
5. The buttons tha says 'Stop Programme' actually starts it... and then stops it, if you press it again! Will be fixed at some point later

## Limitations

1. Requires sudo, handles sensitive components like packet injection, not sandboxed - from a security point of view... yeah, let's not go there
2. A lot of error handling, but the programme needs to be stopped through the GUI in order for it to shut down gracefully
3. Thread safety is maintained, but volume of events over long sessions could cause memory buildup via unbounded queue in HueOutputAdapter
4. Currently has no rule-based filtering, whitelisting, or anomaly categorisation beyond Suricata default rules
5. The 'Register Event' button in the UI logs clicks but isn't tied to any adaptive logic or alert suppression, and doesn't output anything to the user - although this was a deliberate choice as the analysts were not supposed to see how many times they had clicked it; additionally, the function of the button was to simply count the number of detections and not address the alerts themselves

**THIS IS AN EXPERIMENTAL TOOL BEST RUN IN ISOLATED ENVIRONMENTS**
