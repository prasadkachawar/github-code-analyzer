# Embedded C++ Test Project - Comprehensive Code Quality Violations

This project contains **extensive intentional code quality violations** for testing static analysis tools like MISRA C:2012 and CERT C/C++ compliance checkers.

## 🚨 Files and Violations (10 Files Total)

### **📁 Core Application:**
- **`main.cpp`** - Main application with buffer overflow and type conversion issues  
- **`system.cpp`** - System integration with cross-module dependencies and resource management issues

### **📁 Hardware Abstraction Layer:**
- **`gpio.h/gpio.cpp`** - GPIO control with register access and memory violations
- **`uart.h/uart.cpp`** - UART communication with buffer management and string handling issues  
- **`timer.h/timer.cpp`** - Timer/PWM control with interrupt handling and type conversion violations
- **`adc.h/adc.cpp`** - ADC conversion with calibration and multi-channel reading issues

### **📁 Sensor Layer:**  
- **`sensor.h/sensor.cpp`** - Sensor data processing with memory management problems
- **`device.cpp`** - Device configuration with string handling vulnerabilities

## 🎯 **Expected Violations: 50+ Issues**

### **MISRA-C-2012 Violations:**
- **MISRA-C-2012-8.7**: ~20 unused static variables across all files
- **MISRA-C-2012-10.1**: ~15 inappropriate essential type conversions (signed/unsigned, float/int, enum conversions)

### **CERT C/C++ Violations:**
- **CERT-EXP34-C**: ~10 null pointer dereference risks
- **Buffer overflows**: ~5 unsafe string operations (`strcpy`, `sprintf`, `strcat`)
- **Memory leaks**: ~8 malloc without free, use-after-free issues
- **Array bounds**: ~3 unsafe array indexing without bounds checking

### **Additional Issues:**
- **Magic numbers**: Hard-coded constants without `#define`
- **Uninitialized variables**: Struct members used without initialization
- **Resource leaks**: File handles, memory allocations not properly cleaned up
- **Register access**: Unsafe volatile pointer dereferencing
- **Cross-module dependencies**: Calling functions without initialization checks

## 🏗️ **Realistic Embedded Architecture:**

This simulates a real embedded system with:
- **Hardware register access** (GPIO, UART, Timer, ADC)  
- **Interrupt handling** and callback mechanisms
- **Buffer management** for communication protocols
- **Sensor data processing** with calibration routines
- **System initialization** and resource management
- **Cross-module dependencies** typical in embedded firmware

## 🔧 **Build Instructions:**

```bash
# Compile individual modules
gcc -c -std=c++11 -Wall main.cpp
gcc -c -std=c++11 -Wall gpio.cpp  
gcc -c -std=c++11 -Wall uart.cpp
gcc -c -std=c++11 -Wall timer.cpp
gcc -c -std=c++11 -Wall adc.cpp
gcc -c -std=c++11 -Wall sensor.cpp
gcc -c -std=c++11 -Wall device.cpp
gcc -c -std=c++11 -Wall system.cpp

# Link all objects
gcc *.o -o embedded_system
```

## 📊 **Perfect for Testing:**

- **Static analysis tools** (MISRA checkers, CERT analyzers)
- **Code quality gates** in CI/CD pipelines  
- **Security vulnerability scanners**
- **Memory safety analyzers** (Valgrind, AddressSanitizer)
- **Cross-reference analysis** tools

## ⚠️ **SECURITY WARNING**

**DO NOT USE THIS CODE IN PRODUCTION!**

This code contains intentional security vulnerabilities including:
- Buffer overflow attacks
- Null pointer dereference crashes  
- Memory corruption issues
- Use-after-free exploits
- Unsafe string handling

Perfect for **validation and testing purposes only!**

---

**Repository Purpose**: Comprehensive test case for GitHub Code Analyzer and static analysis validation with realistic embedded C++ codebase containing 50+ intentional violations.
