#include "StopsDilepton/tools/plugins/LHEHelper.h"
#include "FWCore/Framework/interface/MakerMacros.h"
//#include "Workspace/HEPHYCMSSWTools/interface/EdmHelper.h"
#include "SimDataFormats/GeneratorProducts/interface/LHERunInfoProduct.h"
#include "FWCore/Framework/interface/Run.h"
#include <iostream>

//void beginRun( const edm::Run&, const edm::EventSetup& );

void 
LHEHelper::analyze(edm::Event const& iEvent, edm::EventSetup const& iSetup) {};

void
LHEHelper::beginRun(const edm::Run & iRun, const edm::EventSetup & iSetup){

  edm::Handle<LHERunInfoProduct> run;
  typedef std::vector<LHERunInfoProduct::Header>::const_iterator headers_const_iterator;

  iRun.getByLabel( "externalLHEProducer", run );
  LHERunInfoProduct myLHERunInfoProduct = *(run.product());

  for (headers_const_iterator iter=myLHERunInfoProduct.headers_begin(); iter!=myLHERunInfoProduct.headers_end(); iter++){
     std::cout << iter->tag() << std::endl;
     std::vector<std::string> lines = iter->lines();
     for (unsigned int iLine = 0; iLine<lines.size(); iLine++) {
        std::cout << lines.at(iLine);
     }
  }
}

DEFINE_FWK_MODULE(LHEHelper);
