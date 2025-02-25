import FWCore.ParameterSet.Config as cms

process = cms.Process("Analysis")

# Define a dummy source to satisfy CRAB
process.source = cms.Source("EmptySource")

# Define maxEvents to prevent errors
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(1))

