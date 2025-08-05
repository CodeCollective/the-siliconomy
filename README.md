<img width="1920" height="400" alt="banner" src="https://github.com/user-attachments/assets/aec3e787-ddb0-4ba5-9b8d-56ba973863d0" />


"The Siliconomy". This workforce development "game" is designed to convey the individual steps involved in the chemical production of computer chips. The name might change to "Workforce Training: Silicon Processing" or something equally technical, with the original name reserved for the factory optimization mobile game.  

The game can be experienced live at https://siliconomy.cc . If you are interested in developing, read on.  

<img width="864" height="752" alt="lasercutter" src="https://github.com/user-attachments/assets/91e91d5a-d96b-4fd8-a00d-86e675f26d77" />  

The "Laser Cutter", the first machine to be modeled and an important step in the production of computer chips.

## Developer's Guide
The development of this game is based on two artifacts:  
1) **The GLTF/GLBs**: Much work goes into developing the models in Python, or otherwise
2) **The AFrame engine**. This determines how the models are used!  

As of now, only the laser cutter model has been produced. 

## Quick start (Tested in Linux)
0) Get required tools: Git, Docker
1) Fork this repository to your account
2) Clone YOUR VERSION!
3) run ```./runServer.sh``` - this will start NGINX and serve the current folder
4) run ```cd assets```
5) run ```./buildDocker.sh``` - this will build the Docker image
6) run ```./runDocker.sh``` - this will build the Laser Cutter model!
7) go to https://127.0.0.1/viewer to see the laser cutter

That's all there is right now. I will be slowly completing all the steps in silicon design, losely:  
<img width="1048" height="591" alt="image" src="https://github.com/user-attachments/assets/9ba9df8e-b5df-4c04-8868-5ece073283e1" />


## Roadmap  
### 1) Production of Metallurgical Silicon

<img width="435" height="338" alt="image" src="https://github.com/user-attachments/assets/64fc813f-9995-421c-ae7a-59d2d16ab8a5" />

### 3) Refinement into Polysilicon

<img width="203" height="246" alt="image" src="https://github.com/user-attachments/assets/a008d956-3389-44f3-bb2a-f398bdb3cc53" />  
 
4) Silicon tetrachloride breakdown (Environmental mindfulness)  

5) Grow the wafer (via Czochralski Process), followed by slicing   

<img width="800" height="1033" alt="image" src="https://github.com/user-attachments/assets/f4a868f3-7ea2-4cf5-8ca2-6b3cf7cf8ca1" />  

6) Doping (CVD)   
<img width="3000" height="2008" alt="image" src="https://github.com/user-attachments/assets/1bbd6cbc-d9c1-4b6c-9dd0-c227eba8ce1a" />  
7) Patterning - Photolithography  

<img width="1000" height="563" alt="image" src="https://github.com/user-attachments/assets/b207a2de-8bb8-4074-a56b-31887a4ecda7" />

8) Etching  
9) Analysis with Electron Microscope  

<img width="600" height="420" alt="image" src="https://github.com/user-attachments/assets/69da94fb-4aeb-46a7-87ed-324b98c27839" />


10) Dicing (Laser Cutter) and Packaging the computer chip (GPU)  
11) Assembly onto PCB  
<img width="712" height="419" alt="image" src="https://github.com/user-attachments/assets/6c1eadc1-f189-4579-add2-ebacf9c71cdc" />

