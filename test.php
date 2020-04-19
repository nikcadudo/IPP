<?PHP

$env = new SetTestEnvironment($argv, $argc);

class SetTestEnvironment {
    //parameters
    private $directory_path = ".";
    private $recursive = false;
    private $parse_script = "./parse.php";
    private $int_script = "./interpret.py";
    private $parse_only = false;
    private $int_only = false;
    private $jexamxml = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    private $help = false;
    private $argv;
    private $argc;

    public function __construct($argv, $argc){   
        $this->argc = $argc;
        $this->argv = $argv;     
        $this->checkParameters();
        //"dir", "parse", "interpret", "jexam"
        $test_params = $this->getParams();
        $all_tests = $this->getAllTests($test_params["dir"]);
        $all_tests = $this->checkAllTestFiles($all_tests);
        $ress = $this->runTests($all_tests, $test_params);
        $html = new FormHTML($ress);
    }

    private function checkParameters(){
        foreach ($this->argv as $arg){
            if ($arg != "./test.php"){
                if($this->help == true){
                    fwrite(STDERR, "ERROR: Invalid combination of parameters!\n");
                    exit(10);
                }
                $arg_splitted = explode("=", $arg);
                if ($arg_splitted[0] == "--directory") {
                    $this->directory_path = $arg_splitted[1];
                } elseif ($arg_splitted[0] == "--recursive"){
                    $this->recursive = true;
                } elseif ($arg_splitted[0] == "--parse-script"){
                    if ($this->int_only || in_array("--int-only", $this->argv)){
                        fwrite(STDERR, "ERROR: Invalid combination of parameters!\n");
                        exit(10);
                    }
                    $this->parse_script = arg_splitted[1];
                } elseif ($arg_splitted[0] == "--int-script"){
                    if ($this->parse_only || in_array("--parse-only", $this->argv)){
                        fwrite(STDERR, "ERROR: Invalid combination of parameters!\n");
                        exit(10);
                    }
                    $this->int_script = arg_splitted[1];
                } elseif ($arg_splitted[0] == "--parse-only"){
                    if ($this->int_only || in_array("--int-only", $this->argv)){
                        fwrite(STDERR, "ERROR: Invalid combination of parameters!\n");
                        exit(10);
                    }
                    $this->parse_only = true;
                } elseif ($arg_splitted[0] == "--int-only"){
                    if ($this->parse_only || in_array("--parse-only", $this->argv)){
                        fwrite(STDERR, "ERROR: Invalid combination of parameters!\n");
                        exit(10);
                    }
                    $this->int_only = true;
                } elseif ($arg_splitted[0] == "--jexamxml"){
                    $this->jexamxml = $arg_splitted[1];
                } elseif ($arg_splitted[0] == "--help"){
                    $this->help = true;
                    fwrite(STDOUT, "HELP\n");
                    exit(0);
                } else {
                    fwrite(STDERR, "ERROR: Parameter not recognized !\n");
                    exit(10);
                }
            }
        }
    }

    private function getParams(){
        if ($this->recursive){
            $test_dir = $this->getDirRecursive();
        } else {
            $test_dir = $this->getDir();
        }
        if ($this->parse_only){
            $test_parse = $this->getParse();
        } elseif ($this->int_only){
            $test_int = $this->getInterpret();
        } else {
            $test_parse = $this->getParse();
            $test_int = $this->getInterpret();
        }
        $test_jexamxml = $this->getJExamXML();
        return ["dir" => $test_dir, "parse" => $test_parse, "interpret" => $test_int, "jexam" => $test_jexamxml];
    }

    private function getDir(){
        try {
            $dir = scandir($this->directory_path);
        } catch(Exception $e) {
            try {
                $dir = scandir('.'.$this->directory_path);
            } catch(Exception $e) {
                fwrite(STDERR, "ERROR: Wrong test directory!\n");
                exit(11);
            }
        }
        $files = array();
        foreach ($dir as $file) {
            if (!is_dir($dir_path)){
                array_push($files, $this->directory_path."/".$file);
            }
        }
        return $files;
    }

    private function getDirRecursive(){
        $rec_iter = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($this->directory_path, RecursiveDirectoryIterator::SKIP_DOTS),
            RecursiveIteratorIterator::SELF_FIRST,
            RecursiveIteratorIterator::CATCH_GET_CHILD
        );
        $dir = array();
        foreach ($rec_iter as $path => $dir_path) {
            if (!is_dir($dir_path)){
                array_push($dir, $path);
            }
        }
        return $dir;
    }

    private function getParse(){
        if(file_exists($this->parse_script) && !is_dir($this->parse_script)) {
			return $this->parse_script;
		} elseif(is_dir($this->parse_script) && file_exists($this->parse_script.'/parse.php')) {
			return $this->parse_script.'/parse.php';
		} 
		fwrite(STDERR, "ERROR: parse.php not found!\n");
		exit(11);
    }

    private function getInterpret(){
        if(file_exists($this->int_script) && !is_dir($this->int_script)) {
			return $this->int_script;
		} elseif(is_dir($this->int_script) && file_exists($this->int_script.'/interpret.py')) {
			return $this->int_script.'/interpret.py';
		} 
		fwrite(STDERR, "ERROR: interpret.py not found!\n");
		exit(11);
    }

    private function getJExamXML(){
        if(file_exists($this->jexamxml) && !is_dir($this->jexamxml)) {
			return $this->jexamxml;
		} elseif(is_dir($this->jexamxml) && file_exists($this->jexamxml.'/jexamxml.jar')) {
			return $this->jexamxml.'/jexamxml.jar';
		} 
		fwrite(STDERR, "ERROR: jexamxml.jar not found!\n");
		exit(11);
    }

    private function getAllTests($dir){
        $test_files = array();
        foreach($dir as $file){
            $testname = explode(".", $file);
            if(count($testname) > 2){
                if ($testname[1] != "" && !in_array($testname[1], $test_files)){
                    array_push($test_files, ".".$testname[1]);
                }
            } else {
                if ($testname[0] != "" && !in_array($testname[0], $test_files)){
                    array_push($test_files, ".".$testname[0]);
                }
            }            
        }    
        return $test_files;
    }

    private function checkAllTestFiles($files){
        foreach ($files as $f){
            if(!file_exists($f.".src")){
                unset($files[array_search($f, $files)]);
            } else{
                if(!file_exists($f.".rc")){
                    $file = fopen($f.'.rc', 'w');
                    file_put_contents($f.'.rc', '0');
				    fclose($file);
                }
                if(!file_exists($f.".in")){
                    $file = fopen($f.'.in', 'w');
				    fclose($file);
                }
                if(!file_exists($f.".out")){
                    $file = fopen($f.'.out', 'w');
				    fclose($file);
                }
            }            
        }
        return $files;
    }

    private function runTests($tests, $params){
        $results = array();
        foreach($tests as $t){
            if($this->parse_only){
                $test = new POTest($t, $params);
            } elseif($this->int_only){
                $test = new IOTest($t, $params);
            } else{
                $test = new Test($t, $params);
            }
            $results[$t] = $test->getResult();
        }      
        return $results;
    }
}

class Test {
    private $passed = false;
    private $name;
    private $params;
    private $parse_flag = 1;

    public function __construct($name, $params){
        $this->name = $name;
        $this->params = $params;
        //"rc", "out"
        $this->$result = $this->execute();
        $this->passed = $this->validate();
    }

    public function execute(){
        $source = $this->name.'.src';
        $out = array();
        $rc = -1;
        exec("php7.4 ".$this->params['parse']." <".$source , $out, $rc);
        $ref_rc = fgets(fopen($this->name.".rc", 'r'));
        if($result['rc'] == $ref_rc){
            $this->result = ["rc" => $rc, "out" => $out];
            if(validate()){
                $this->parse_flag = 0;
                $out_file = fopen($this->name.".test", 'w');
                file_put_contents($this->name.".test", $this->result["out"]);
                fclose($out_file);
                $source = $this->name.".test";
                $input = $this->name.'.in';
                $out = array();
                $rc = -1;
                exec("python3.8 ".$this->params['interpret']." --source=".$source." --input=".$input , $out, $rc);
                return ["rc" => $rc, "out" => $out];
            } else {
                $this->passed = false;
            }
        } else {
            $this->passed = false;
        }
    }

    public function validate(){
        if($this->parse_flag){
            $ref_rc = fgets(fopen($this->name.".rc", 'r'));
            if($this->result['rc'] == $ref_rc){
                if($this->result['rc'] == 0){
                    $out_file = fopen($this->name.".test", 'w');
                    file_put_contents($this->name.".test", $this->result["out"]);
                    fclose($out_file);
                    exec("java -jar ".$this->params["jexam"]." ".$this->name.".out ".$this->name.".test"." out.xml -D");
                    $tmp = array();
                    $diff = -1;
                    exec("diff out.xml valid.xml", $tmp, $diff);
                    exec('rm out.xml');
                    exec('rm '.$this->name.".test");
                    if($diff == 0){
                        return true;
                    } else {
                        return false;
                    }                
                } else{
                    return true;
                }
            } else {
                return false;
            }
        } else {
            $ref_rc = fgets(fopen($this->name.".rc", 'r'));
            if($this->result["rc"] == $ref_rc){
                if((int)$this->result["rc"] == 0){
                    $out_file = fopen($this->name.".test", 'w');
                    file_put_contents($this->name.".test", $this->result["out"]);
                    fclose($out_file);
                    $tmp = array();
                    $diff = -1;
                    exec("diff ".$this->name.".out ".$this->name.".test", $tmp, $diff);
                    if($diff == 0){
                        return true;
                    } else {
                        return false;
                    }
                    exec('rm '.$this->name.".test");
                } else {
                    return true;
                }
            } else {
                return false;
            }
        }		
    }

    public function getResult(){
        return $this->passed;
    }
}

class POTest extends Test {
    private $passed = false;
    private $name;
    private $params;
    private $result;

    public function __construct($name, $params){
        $this->name = $name;
        $this->params = $params;
        //"rc", "out"
        $this->result = $this->execute();
        $this->passed = $this->validate();
    }

    public function execute(){
        $source = $this->name.'.src';
        $out = array();
        $rc = -1;
        exec("php7.4 ".$this->params['parse']." <".$source , $out, $rc);
        return ["rc" => $rc, "out" => $out];
    }

    public function validate(){
        $ref_rc = fgets(fopen($this->name.".rc", 'r'));
        if($this->result['rc'] == $ref_rc){
            if($this->result['rc'] == 0){
                $out_file = fopen($this->name.".test", 'w');
                file_put_contents($this->name.".test", $this->result["out"]);
                fclose($out_file);
                exec("java -jar ".$this->params["jexam"]." ".$this->name.".out ".$this->name.".test"." out.xml -D");
                $tmp = array();
                $diff = -1;
                exec("diff out.xml valid.xml", $tmp, $diff);
                exec('rm out.xml');
                exec('rm '.$this->name.".test");
                if($diff == 0){
                    return true;
                } else {
                    return false;
                }                
            } else{
                return true;
            }
        } else {
            return false;
        }
    }

    public function getResult(){
        return $this->passed;
    }

    public function getOutput(){
        return $this->result["out"];
    }

    public function getReturnCode(){
        return $this->result["rc"];
    }
}

class IOTest extends Test {
    private $passed = false;
    private $name;
    private $params;
    private $result;

    public function __construct($name, $params){
        $this->name = $name;
        $this->params = $params;
        //"rc", "out"
        $this->result = $this->execute();
        $this->passed = $this->validate();
    }

    public function execute(){
        $source = $this->name.'.src';
        $input = $this->name.'.in';
        $out = array();
        $rc = -1;
        exec("python3.8 ".$this->params['interpret']." --source=".$source." --input=".$input , $out, $rc);
        return ["rc" => $rc, "out" => $out];
    }

    public function validate(){
        $ref_rc = fgets(fopen($this->name.".rc", 'r'));
        if($this->result["rc"] == $ref_rc){
            if((int)$this->result["rc"] == 0){
                $out_file = fopen($this->name.".test", 'w');
                file_put_contents($this->name.".test", $this->result["out"]);
                fclose($out_file);
                $tmp = array();
                $diff = -1;
                exec("diff ".$this->name.".out ".$this->name.".test", $tmp, $diff);
                if($diff == 0){
                    return true;
                } else {
                    return false;
                }
                exec('rm '.$this->name.".test");
            } else {
                return true;
            }
        } else {
            return false;
        }
    }

    public function getResult(){
        return $this->passed;
    }

    public function getOutput(){
        return $this->result["out"];
    }

    public function getReturnCode(){
        return $this->result["rc"];
    }
}

class FormHTML {
    private $tests;
    public function __construct($tests){
        $this->tests = $tests;
        $this->initializeTable();
		$this->addTests();
        $this->endTable();
    }

    private function initializeTable(){
        fwrite(STDOUT, '<!DOCTYPE html>');
        fwrite(STDOUT, '<html>');
        fwrite(STDOUT, '<body>');
        fwrite(STDOUT, '<table style="undefined; width: 251px; border-collapse:collapse; border-spacing:0; font-family:Arial, sans-serif; font-size:14px; border-style:solid; border-color:black; text-align:center;">');
        fwrite(STDOUT, '<colgroup>');
        fwrite(STDOUT, '<col style="width: 352px">');
        fwrite(STDOUT, '<col style="width: 121px">');
        fwrite(STDOUT, '</colgroup>');
		fwrite(STDOUT, '<tr style="font-size:18px; background-color:#ffffff;">');	
		fwrite(STDOUT, '<th>Test Name</th>');	
		fwrite(STDOUT, '<th>Result</th>');	
        fwrite(STDOUT, '</tr>');
    }

    private function addTests(){
        foreach($this->tests as $test => $res){
            fwrite(STDOUT, '<tr>');
            if($res == true){
                fwrite(STDOUT, '<td style="border-style:solid; background-color:#009901;">'.$test.'</td>');
                fwrite(STDOUT, '<td style="border-style:solid; background-color:#009901;">passed</td>');
            } else {
                fwrite(STDOUT, '<td style="border-style:solid; background-color:#cb0000;">'.$test.'</td>');
                fwrite(STDOUT, '<td style="border-style:solid; background-color:#cb0000;">failed</td>');
            }
            fwrite(STDOUT, '</tr>');
        }
    }

    private function endTable(){
        fwrite(STDOUT, '</table>');	
		fwrite(STDOUT, '</body>');
		fwrite(STDOUT, '</html>');
		fclose(STDOUT);
    }
}

?>