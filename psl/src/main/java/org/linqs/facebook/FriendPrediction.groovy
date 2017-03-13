package org.linqs.facebook;

import org.linqs.psl.application.inference.MPEInference;
import org.linqs.psl.config.ConfigBundle;
import org.linqs.psl.config.ConfigManager;
import org.linqs.psl.database.DataStore;
import org.linqs.psl.database.Database;
import org.linqs.psl.database.Queries;
import org.linqs.psl.database.loading.Inserter;
import org.linqs.psl.database.rdbms.RDBMSDataStore;
import org.linqs.psl.database.rdbms.driver.H2DatabaseDriver;
import org.linqs.psl.database.rdbms.driver.H2DatabaseDriver.Type;
import org.linqs.psl.groovy.PSLModel;
import org.linqs.psl.model.atom.Atom;
import org.linqs.psl.model.predicate.Predicate;
import org.linqs.psl.model.term.ConstantType;
import org.linqs.psl.utils.dataloading.InserterUtils;

import java.io.PrintStream;
import java.nio.file.Paths;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FriendPrediction {
   private static final String PARTITION_OBSERVED = "observed";
   private static final String PARTITION_TARGETS = "targets";

   private static Logger log = LoggerFactory.getLogger(this.class);

   private ExperimentConfig config;
   private PSLModel model;
   private DataStore data;

   public FriendPrediction(ConfigBundle cb) {
      this.config = new ExperimentConfig(cb);

      String dbPath = Paths.get(config.dbPath, 'facebook').toString();
      this.data = new RDBMSDataStore(new H2DatabaseDriver(Type.Disk, dbPath, true), config.cb);
      this.model = new PSLModel(this, this.data);
   }

   private void definePredicates() {
      // Employment(Person, Place)
      model.add predicate: "Employment", types: [ConstantType.UniqueID, ConstantType.UniqueID];
      // Education(Person, Place)
      model.add predicate: "Education", types: [ConstantType.UniqueID, ConstantType.UniqueID];
      // Lived(Person, Place)
      model.add predicate: "Lived", types: [ConstantType.UniqueID, ConstantType.UniqueID];

      // Friends(Person, Person)
      model.add predicate: "Friends", types: [ConstantType.UniqueID, ConstantType.UniqueID];
    }

    private void defineRules() {
      //Prior that two people are not Friends

      model.add(
         rule: ~Friends(A,B),
         squared: true,
         weight : 0.1
      );

      //Collective friendship rules

      model.add(
         rule: (Employment(ID1, Place1) & Employment(ID2, Place1) & Employment(ID3, Place1) & Friends(ID1, ID2) & Friends(ID1, ID3) & (ID1-ID2) & (ID1-ID3)) >> Friends(ID2, ID3),
         squared: true,
         weight: 1.0
      );

      model.add(
         rule: (Education(ID1, Place1) & Education(ID2, Place1) & Education(ID3, Place1) & Friends(ID1, ID2) & Friends(ID1, ID3) & (ID1-ID2) & (ID1-ID3)) >> Friends(ID2, ID3),
         squared: true,
         weight: 1.0
      );

      model.add(
         rule: (Lived(ID1, Place1) & Lived(ID2, Place1) & Lived(ID3, Place1) & Friends(ID1, ID2) & Friends(ID1, ID3) & (ID1-ID2) & (ID1-ID3)) >> Friends(ID2, ID3),
         squared: true,
         weight: 1.0
      );

      //Similar property rules

      model.add(
         rule: (Employment(ID1, Place1) & Employment(ID2, Place1)) >> Friends(ID1, ID2),
         squared:true,
         weight:1.0
      );

      model.add(
         rule:(Education(ID1, Place1) & Education(ID2, Place1)) >> Friends(ID1, ID2),
         squared:true,
         weight:1.0
      );

      model.add(
         rule: (Lived(ID1, Place1) & Lived(ID2, Place1)) >> Friends(ID1, ID2),
         squared:true,
         weight:1.0
      );

      //Transitive friendship rule

      model.add(
         rule: (Friends(ID1, ID2) & Friends(ID2, ID3) & (ID1-ID2) & (ID2-ID3)) >> Friends(ID1, ID3),
         squared:true,
         weight:1.0
      );

      //Symmetric friendship rule

      model.add(
         rule: Friends(ID1, ID2) >> Friends(ID2, ID1),
         squared:true,
         weight:1.0
      );
   }

   private void loadData() {
      Inserter inserter = null;

      // TEST
      System.out.println("Inserting employment");

      inserter = data.getInserter(Employment, data.getPartition(PARTITION_OBSERVED));
      InserterUtils.loadDelimitedData(inserter, Paths.get(config.dataPath, "employment.txt").toString(), '\t');

      inserter = data.getInserter(Education, data.getPartition(PARTITION_OBSERVED));
      InserterUtils.loadDelimitedData(inserter, Paths.get(config.dataPath, "education.txt").toString(), '\t');

      // TEST
      System.out.println("Inserting Lived from: " + Paths.get(config.dataPath, "lived.txt").toString());

      inserter = data.getInserter(Lived, data.getPartition(PARTITION_OBSERVED));
      InserterUtils.loadDelimitedData(inserter, Paths.get(config.dataPath, "lived.txt").toString(), '\t');

      // TEST
      System.out.println("Inserting Friends from: " + Paths.get(config.dataPath, "friends_targets.txt").toString());

      Inserter inserter2 = data.getInserter(Friends, data.getPartition(PARTITION_TARGETS));
      InserterUtils.loadDelimitedData(inserter2, Paths.get(config.dataPath, "friends_targets.txt").toString(), '\t');
   }

   private void runInference() {
      def closed = [Employment, Education, Lived] as Set;

      Database inferenceDB = data.getDatabase(data.getPartition(PARTITION_TARGETS), closed, data.getPartition(PARTITION_OBSERVED));

      def inferenceApp = new MPEInference(model, inferenceDB, config.cb);
      inferenceApp.mpeInference();
      inferenceDB.close();
   }

   private void writeOutput() {
      Database resultsDB = data.getDatabase(data.getPartition(PARTITION_TARGETS));
      PrintStream ps = new PrintStream(new File(Paths.get(config.outputPath, "friends_infer.txt").toString()));
      Set<Atom> atomSet = Queries.getAllAtoms(resultsDB, Friends);
      for (Atom atom : atomSet) {
         ps.println(atom);
      }
      resultsDB.close();
   }

   public void mainExperiment() {
      definePredicates();
      defineRules();

      loadData();

      // TEST
      data.close();
      return;

      runInference();
      writeOutput();

      data.close();
   }

   private static ConfigBundle populateConfigBundle(String[] args) {
      ConfigBundle cb = ConfigManager.getManager().getBundle("facebook");

      if (args.length > 0) {
         System.out.println(args[0]);
         cb.setProperty('experiment.data.path', args[0]);
      }

      if (args.length > 1) {
         cb.setProperty('experiment.name', args[1]);
      }

      return cb;
   }

   public static void main(String[] args) {
      ConfigBundle cb = populateConfigBundle(args);
      FriendPrediction pslProgram = new FriendPrediction(cb);
      pslProgram.mainExperiment();
   }

   public static class ExperimentConfig {
      public ConfigBundle cb;

      public String experimentName;
      public String dbPath;
      public String dataPath;
      public String outputPath;

      public ExperimentConfig(ConfigBundle cb) {
         this.cb = cb;

         this.experimentName = cb.getString('experiment.name', 'facebook');
         this.dbPath = cb.getString('experiment.dbpath', '/media/temp/temp');
         this.dataPath = cb.getString('experiment.data.path', 'data');
         this.outputPath = cb.getString('experiment.output.outputdir', 'output');
      }
   }
}
