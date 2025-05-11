echo off


call C:\ProgramData\Anaconda3\Scripts\activate.bat


echo ***
echo Starting jupyter notebook in teaching system filespace
echo ***
echo Trying several locations: some error messages to be expected, but it should still find your path.
echo ***


call jupyter notebook --notebook-dir=\\ifs.eng.cam.ac.uk\users\%username%\Desktop\
