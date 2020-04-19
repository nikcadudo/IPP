<?php
$output_file = new XMLWriter;
$order = 1;

//kontrola vstupnich argumentu skriptu
checkArgs($argc, $argv);

//otevreni a nacteni vstupniho souboru
$input_file = fopen('php://stdin', 'r');
if($input_file == NULL){
	fwrite(STDERR, "ERROR: Cannot open input file!\n");
	exit(11);
}

//kontrola hlavicky vstupniho souboru
checkHeader($input_file);

$output_file = startXML();

while($line = fgets($input_file)){
	$line = findAndDeleteComment($line);
	if($line != ""){
		$array = preg_split("/\s+/", trim($line));
		if(preg_match("/^(MOVE|CREATEFRAME|PUSHFRAME|POPFRAME|DEFVAR|CALL|RETURN|PUSHS|POPS|ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|NOT|INT2CHAR|STRI2INT|READ|WRITE|CONCAT|STRLEN|GETCHAR|SETCHAR|TYPE|LABEL|JUMP|JUMPIFEQ|JUMPIFNEQ|EXIT|DPRINT|BREAK)$/", trim(strtoupper($array[0])))){
			parseLine($array);
		}else{
			fwrite(STDERR, "ERROR: Instruction not valid!\n");
			exit(22);
		}
	}
}

endXML();
exit(0);


#-------------------------FUNKCE---------------------------------#
function checkArgs($argc, $argv){
	switch ($argc) {
		case 2:
			if(in_array("--help", $argv) || in_array("-help", $argv)){
				fwrite(STDOUT, "HELP\n");
				exit(0);
			} else {
				fwrite(STDERR, "ERROR: Wrong arguments!\n");
				exit(10);
			}
			break;
		case 1:
			break;		
		default:
			fwrite(STDERR, "ERROR: Wrong arguments!\n");
			exit(10);
			break;
	}
}

function checkHeader($input_file){
	$header = strtolower(fgets($input_file));
	$header = findAndDeleteComment($header);
	if(trim($header) != ".ippcode20"){
		fwrite(STDERR, "ERROR: Header is missing or wrong!\n");
		exit(21);
	}
}

function startXML(){
	$XMLfile = new XMLWriter;
	$XMLfile = xmlwriter_open_memory();
	if($XMLfile == null){
		fwrite(STDERR, "ERROR: Cannot open output file\n");
		exit(12);
	}
	xmlwriter_set_indent($XMLfile, true);
	$indentStr = xmlwriter_set_indent_string($XMLfile, '  ');
	xmlwriter_start_document($XMLfile, '1.0', 'UTF-8');
	xmlwriter_start_element($XMLfile, 'program');
	xmlwriter_start_attribute($XMLfile, 'language');
	xmlwriter_text($XMLfile, 'IPPcode20');
	return $XMLfile;
}

function endXML(){
	xmlwriter_end_element($GLOBALS['output_file']);
	xmlwriter_end_document($GLOBALS['output_file']);
	echo xmlwriter_output_memory($GLOBALS['output_file']);
}

function findAndDeleteComment($line){
	if($line == ""){
		return $line;
	}

	if(preg_match("/^(.*)#(.*)$/", $line)){
		$var = trim($line);
		$arr = preg_split("/#/", $var);
		return $arr[0];
	}

	return $line;
}

function parseLine($arr_line){
	switch (trim(strtoupper($arr_line[0]))) {
		case 'MOVE':
			if(count($arr_line) != 3){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("MOVE");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			}else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif (isConstant($arr_line[2])){
				writeConstToXML($arr_line[2], "arg2");
			}else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'CREATEFRAME':
			if(count($arr_line) != 1){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("CREATEFRAME");
			endInstr();
			break;

		case 'PUSHFRAME':
			if(count($arr_line) != 1){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("PUSHFRAME");
			endInstr();
			break;

		case 'POPFRAME':
			if(count($arr_line) != 1){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("POPFRAME");
			endInstr();
			break;

		case 'DEFVAR':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("DEFVAR");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			}else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'CALL':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("CALL");

			if(isLabel($arr_line[1])){
				writeLabelToXML($arr_line[1]. "arg1");
			}else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'RETURN':
			if(count($arr_line) != 1){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("RETURN");
			endInstr();
			break;

		case 'PUSHS':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("PUSHS");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} elseif(isConstant($arr_line[1])) {
				writeConstToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'POPS':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("POPS");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'ADD':
		case 'SUB':
		case 'MUL':
		case 'IDIV':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of third argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'LT':
		case 'GT':
		case 'EQ':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of third argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'AND':
		case 'OR':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of third argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'NOT':
			if(count($arr_line) != 3){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("NOT");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'INT2CHAR':
			if(count($arr_line) != 3){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("INT2CHAR");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'STRI2INT':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("STRI2INT");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'READ':
			if(count($arr_line) != 3){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("READ");

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isType($arr_line[2])){
				writeTypeToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'WRITE':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} elseif(isConstant($arr_line[1])) {
				writeConstToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'CONCAT':
		case 'GETCHAR':
		case 'SETCHAR':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'STRLEN':
		case 'TYPE':
			if(count($arr_line) != 3){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isType($arr_line[2])){
				writeTypeToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'LABEL':
		case 'JUMP':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isLabel($arr_line[1])){
				writeLabelToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'JUMPIFEQ':
		case 'JUMPIFNEQ':
			if(count($arr_line) != 4){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isLabel($arr_line[1])){
				writeLabelToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[2])){
				writeVarToXML($arr_line[2], "arg2");
			} elseif(isConstant($arr_line[2])) {
				writeConstToXML($arr_line[2], "arg2");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of second argument!\n");
				exit(23);
			}

			if(isVariable($arr_line[3])){
				writeVarToXML($arr_line[3], "arg3");
			} elseif(isConstant($arr_line[3])) {
				writeConstToXML($arr_line[3], "arg3");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of third argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'EXIT':
		case 'DPRINT':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr(strtoupper($arr_line[0]));

			if(isVariable($arr_line[1])){
				writeVarToXML($arr_line[1], "arg1");
			} elseif(isConstant($arr_line[1])) {
				writeConstToXML($arr_line[1], "arg1");
			} else{
				fwrite(STDERR, "ERROR: Invalid type of first argument!\n");
				exit(23);
			}

			endInstr();
			break;

		case 'BREAK':
			if(count($arr_line) != 2){
				fwrite(STDERR, "ERROR: Invalid number of arguments!\n");
				exit(23);
			}

			startInstr("BREAK");
			endInstr();
			break;
		
		default:
			fwrite(STDERR, "ERROR: Invalid operating code!\n");
			exit(22);
			break;
	}
}

function isVariable($arg){
	if(preg_match("/^(TF|LF|GF)@(([a-zA-Z]|-|[_$&%*!?])([a-zA-Z]|-|[_$&%*!?]|[0-9])*)$/u", $arg) == 1){
		return true;
	}
	return false;
}

function isConstant($arg){
	if(preg_match("/^(bool)@(true|false)$/", $arg) == 1) {
		return true;
	} elseif (preg_match("/^(nil)@(nil)$/", $arg) == 1) {
		return true;
	} elseif (preg_match("/^string@(\p{L}|[^(\w\\\)]|\d|[_]|\\\\([0-9]{3}))*$/u", $arg) == 1) {
		return true;
	} elseif (preg_match("/^int@[+-]?(\d)*$/", $arg) == 1) {
		return true;
	} else {
		return false;
	}
}

function isLabel($arg){
	if(preg_match("/^(([a-zA-Z]|-|[_$&%*!?])([a-zA-Z]|-|[_$&%*!?]|[0-9])*)$/", $arg) == 1){
		return true;
	}
	return false;
}

function isType($arg){
	if(preg_match("/^(int|string|bool|nil)$/", $arg) == 1) {
		return true;
	}
	return false;
}

function startInstr($instr){
	xmlwriter_start_element($GLOBALS['output_file'], 'instruction');
	xmlwriter_start_attribute($GLOBALS['output_file'], 'order');
	xmlwriter_text($GLOBALS['output_file'], (string)($GLOBALS['order']++));
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_start_attribute($GLOBALS['output_file'], 'opcode');
	xmlwriter_text($GLOBALS['output_file'], $instr);
}

function endInstr(){
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_end_element($GLOBALS['output_file']);
}

function writeVarToXML($arg, $arg_count){
	xmlwriter_start_element($GLOBALS['output_file'], $arg_count);
	xmlwriter_start_attribute($GLOBALS['output_file'], 'type');
	xmlwriter_text($GLOBALS['output_file'], 'var');
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_text($GLOBALS['output_file'], $arg);
	xmlwriter_end_element($GLOBALS['output_file']);
}

function writeConstToXML($arg, $arg_count){
	xmlwriter_start_element($GLOBALS['output_file'], $arg_count);
	xmlwriter_start_attribute($GLOBALS['output_file'], 'type');
	$constArray = explode('@', trim($arg), 2);
	xmlwriter_text($GLOBALS['output_file'], $constArray[0]);
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_text($GLOBALS['output_file'], $constArray[1]);
	xmlwriter_end_element($GLOBALS['output_file']);
}

function writeLabelToXML($arg, $arg_count){
	xmlwriter_start_element($GLOBALS['output_file'], $arg_count);
	xmlwriter_start_attribute($GLOBALS['output_file'], 'type');
	xmlwriter_text($GLOBALS['output_file'], 'label');
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_text($GLOBALS['output_file'], $arg);
	xmlwriter_end_element($GLOBALS['output_file']);
}

function writeTypeToXML($arg, $arg_count){
	xmlwriter_start_element($GLOBALS['output_file'], $arg_count);
	xmlwriter_start_attribute($GLOBALS['output_file'], 'type');
	xmlwriter_text($GLOBALS['output_file'], $arg);
	xmlwriter_end_attribute($GLOBALS['output_file']);
	xmlwriter_end_element($GLOBALS['output_file']);
}

?>