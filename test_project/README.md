# Test Embedded C++ Project

This project contains intentional code quality violations for testing static analysis tools.

## Files:
- `main.cpp` - Main application with buffer overflow and type conversion issues
- `sensor.cpp` - Sensor handling with memory management problems  
- `device.cpp` - Device configuration with string handling vulnerabilities
- `sensor.h` - Header file for sensor declarations

## Known Issues (Intentional):
- MISRA-C-2012-8.7: Unused static variables
- MISRA-C-2012-10.1: Inappropriate essential type conversions
- CERT-EXP34-C: Null pointer dereference risks
- Buffer overflow vulnerabilities
- Memory management issues
- Use-after-free problems

This code is designed to trigger multiple static analysis violations for testing purposes.
