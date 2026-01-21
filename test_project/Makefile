CC=gcc
CFLAGS=-Wall -Wextra -std=c++11

SOURCES=main.cpp sensor.cpp device.cpp
OBJECTS=$(SOURCES:.cpp=.o)
TARGET=embedded_test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET)

%.o: %.cpp
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
