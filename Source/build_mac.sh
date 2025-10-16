#!/bin/bash

NAME="EPL ABR Analysis"
APPNAME="$NAME.app"
VER="1.11"

if [[ "$1" != "-package" && "$1" != "-dmg" ]]; then
    echo "Building app..."
#    pythonw setup.py py2app -S
    pyinstaller --noconfirm notebook_mac.spec
    
    echo "Moving misplaced libraries..."
#    mv "dist/$APPNAME/Contents/Frameworks/libwx"* "dist/$APPNAME/Contents/Resources/lib/python3.7/lib-dynload/wx"
    
    echo "Copying help folder..."
    cp -r help "dist/$APPNAME/Contents/Resources/help"
    
    echo "Deleting build folder..."
    rm -r build
fi

if [ "$1" == "-build" ]; then
    echo "Skipping package builds."
    echo "Done."
    exit 1
fi

if [ "$1" != "-dmg" ]; then
    echo "Building packages..."
    echo "Copying app to tmp..."
    ditto "dist/$APPNAME" "/tmp/PkgRoot/Applications/EPL/$APPNAME"
    
    echo "Building package installer..."
    od=${PWD}
    cd /tmp
    pkgbuild --root PkgRoot "$NAME $VER.pkg"
    cd "$od"
fi

if [ "$1" != "-package" ]; then   
    echo "Remove folder"
    cd dist
    rm -r "$NAME"
    cd ..
    
    echo "Rename dist folder..."
    mv dist "$NAME $VER"
    
    echo "Create dmg..."
    hdiutil create -volname "$NAME $VER" -srcfolder "$NAME $VER" -ov -format UDZO "$NAME $VER.dmg"  
fi

echo "Done."