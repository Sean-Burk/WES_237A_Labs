CXX?=g++
CXXFLAGS=-O0

EXEC=lab3

INCLUDEDIR=include
SRCDIR=src
OBJDIR=objs

LIBS=-lc

SRCS=$(wildcard $(SRCDIR)/*.cpp)
OBJS=$(patsubst $(SRCDIR)/*.cpp, $(OBJDIR)/*.o, $(SRCS))
INCLUDES=-I$(INCLUDEDIR)

all: $(SRCS) $(EXEC)

$(EXEC): $(OBJS)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(OBJS) -o $(EXEC) $(LIBS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(EXEC)
	rm -f $(OBJDIR)/*.o
