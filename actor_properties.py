'''
Module containing infos about the actor properties
Infos consist of Info about how to parse, max value for a property length

Take Actor type ID
Look in hardcoded table for the corresponding class to actor archtype
take leaf element from netcache containing said class
takk all elements of that leaf and of all the parents up to the root
look in resulting list for network id, this should result in somethting unique
'''