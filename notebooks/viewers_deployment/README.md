## Viewers deployment tutorials

This folder contains notebooks accompanying tutorials linked below demonstrating how to deploy your own instances of the OHIF and Slim viewers in the cloud:

* [Google Cloud deployment of OHIF Viewer](https://tinyurl.com/idc-ohif-gcp)
* [Google Cloud deployment of Slim Viewer](https://tinyurl.com/idc-slim-gcp)

Those tutorials utilize Google Firebase to deploy viewer webapps. There are several advantages of using Google Firebase over Docker:
* Firebase hosting does not require a virtual machine, and the base tier is free - which means you can get a working instance of Slim running at no cost!
* While Docker may be convenient to use on your own machine to experiment with the viewer, setting up Docker is - unfortunately - not always trivial, and your local instance cannot be shared with others.
* Once your free cloud-based viewer instance is ready, you can use it from any computer without having to install anything, you can share access to that instance with your colleagues, and it does not require any maintenance (the upgrade process is documented!).

