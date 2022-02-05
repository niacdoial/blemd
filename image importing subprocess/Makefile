CXX := g++

ifeq ($(OS),Windows_NT)
	BINEXT := exe
else
	BINEXT := lin
endif

.PHONY: all
all: bmdview.cpp
	$(CXX) bmdview.cpp -o ../bmdview.$(BINEXT)
