pragma solidity >=0.4.22 <0.7.0;

contract Certificate {
    
    // 情境：某學校針對某學生發起一份合約，學校為合約的發起人 (school)，
    // 而學生的資料則在建立合約時帶入 (profile)，
    // 其中此合約紀錄了該學生的修課紀錄 (courses) 以及學業狀態 (educationStatus) 也就是畢業與否
    // 學校透過更新合約的 courses 陣列參數，添加新的修課紀錄
    // 而在滿足畢業條件後，透過更新 educationStatus 參數，即可表示該學生於此學校畢業
    // 細部還有很多地方可能要再討論！
    // 參考文獻：https://ithelp.ithome.com.tw/articles/10222379
    
    address internal school; // 學校發起合約時的地址
    
    Profile public profile; // 個人資料
    
    Course[] internal courses; // 修課紀錄
    
    EducationStatus public educationStatus; // 學業狀態
    
    // 建構時帶入個人資料
    constructor(string memory name, address account, string memory schoolName, string memory major, string memory minor, uint8 enrollYear) public {
        school = msg.sender;
        profile = Profile({
            name: name,
            account: account,
            schoolName: schoolName,
            major: major,
            minor: minor,
            enrollYear: enrollYear,
            educationStatus: EducationStatus.learning
        });
    }
    
    // 個人資料結構
    struct Profile {
        string name; // 學生姓名
        address account; // 學生地址
        string schoolName; // 學校名稱
        string major; // 主修
        string minor; //輔系
        uint8 enrollYear; //入學年份
        EducationStatus educationStatus; //學業狀態
        
    }
    
    // 課程結構
    struct Course {
        string name; // 課程名稱
        string content; // 課程內容
        string comment; // 老師評語
        uint8 grade; // 成績
    }
    
    // 學業狀態選項
    enum EducationStatus {
        undergraduate, // 肄業
        learning, // 在學中
        graduate // 畢業
    }
    
    // 檢查操作者是否為發起合約的學校
    modifier checkSchool {
        require(msg.sender == school, "Not school!");
        _;
    }
    
    // 檢查操作者是否為該合約指定之學生
    modifier checkStudent {
        require(msg.sender == profile.account, "Not student!");
        _;
    }
    
    // 檢查操作者為在校學生
    modifier checkEducationStatus {
        require(profile.educationStatus == EducationStatus.learning, "Not student!");
        _;
    }
    
    
    // 檢查 Index 長度
    modifier IndexValidator(uint index, uint max) {
        require(index < max, "Out of range.");
        _;
    }
    
    // 設定事件完成後的顯示結果
    event done(DoneCode eventCode, string message);

    enum DoneCode {
        setCourse, // 設置修課證明
        setCertificate, // 設置畢業證書
        setSchool, // 設置學校名稱
        setMajor, // 設置主修
        setMinor, // 設置輔系
        setName, // 設置姓名
        setEnrollYear, //設置入學年份
        setEducationStatus //設置學籍狀態
    }
    
    // 取得所有課程數量
    function getCourseCount() public view returns(uint) {
        return courses.length;
    }
    
    // 取得某課程資訊
    function getCourse(uint index) public view IndexValidator(index, getCourseCount())
        returns(string memory, string memory, string memory, uint8) {
        Course memory course = courses[index];
        return(course.name, course.content, course.comment, course.grade);
    }
    
    // 上傳某課程紀錄
    function setCourse(string memory name, string memory content, string memory comment, uint8 grade) public checkSchool {
        courses.push(Course({ name: name, content: content, comment: comment, grade: grade }));
        emit done(DoneCode.setCourse, "Set Course");
    }
    
    
    // 檢查是否滿足某證書的條件
    modifier checkFinish() {
        require(courses.length > 10, "Not yet finish"); // 這裡的條件可能要討論一下怎麼寫（根據不同系所）
        _;
    }
    
    // 學生修改學業狀態（頒發證書）
    function setCertificate() public checkFinish checkStudent{
        educationStatus = EducationStatus.graduate;
        emit done(DoneCode.setCertificate, "Set Certificate");
    }
    
    // 修改個人資料的學校資訊
    function setSchool(string memory newSchool) public checkSchool {
        profile.schoolName = newSchool;
        emit done(DoneCode.setSchool, "Set School");
    }
    
    // 修改個人資料的主修資訊
    function setMajor(string memory newMajor) public checkSchool {
        profile.major = newMajor;
        emit done(DoneCode.setMajor, "Set Major");
    }
    
    // 修改個人資料的輔系資訊
     function setMinor(string memory newMinor) public checkSchool {
        profile.minor = newMinor;
        emit done(DoneCode.setMinor, "Set Minor");
    }
    
    // 修改個人資料的姓名資訊
    function setName(string memory newName) public checkSchool {
        profile.name = newName;
        emit done(DoneCode.setName, "Set Name");
    }
        
    // 修改個人資料的入學狀態
    function setEducationStatus(EducationStatus newEducationStatus) public checkSchool {
        profile.educationStatus = newEducationStatus;
        emit done(DoneCode.setEducationStatus, "Set EducationStatus");
    }
    
}
