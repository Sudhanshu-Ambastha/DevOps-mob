export const CATEGORIES=[
    "Education",
    "Campus Life",
    "Transport",
    "Events",
    "Resources",
    "Facilities",
    "Other"
];

export const STATUSES=["open","in-progress","solved"];

export const mockUsers=[
    {
        _id:"u1",
        name:"Riya Sharma",
        email:"riya@devbridge.com",
        role:"user",
        bio:"BCA student who notices too many small campus problems.",
        skills:[],
        createdAt:"2026-07-01T10:00:00.000Z"
    },
    {
        _id:"u2",
        name:"Arjun Mehta",
        email:"arjun@devbridge.com",
        role:"developer",
        bio:"Full stack developer. I like building tools for students.",
        skills:["React","Node.js","MongoDB"],
        createdAt:"2026-07-03T09:30:00.000Z"
    },
    {
        _id:"u3",
        name:"Neha Verma",
        email:"neha@devbridge.com",
        role:"developer",
        bio:"Frontend developer and UI enthusiast.",
        skills:["JavaScript","CSS","Figma"],
        createdAt:"2026-07-05T14:15:00.000Z"
    },
    {
        _id:"u4",
        name:"Kabir Singh",
        email:"kabir@devbridge.com",
        role:"user",
        bio:"Hostel resident and daily bus commuter.",
        skills:[],
        createdAt:"2026-07-08T08:45:00.000Z"
    }
];

export const mockProblems=[
    {
        _id:"p1",
        title:"Students struggle to find teammates for college projects",
        description:"Every semester we have to form teams for projects and hackathons. Most students only know people from their own section, so teams are formed randomly and skilled students from other sections never meet. There is no place to see who is looking for a team and what skills they have.",
        category:"Education",
        outcome:"A searchable directory where students can share skills, project ideas, and find collaborators across departments.",
        constraints:"Should work well on mobile and let students control which contact details are visible.",
        paid:true,
        budget:"₹5,000–₹15,000",
        tags:["teamwork","projects","hackathon"],
        author:{_id:"u1",name:"Riya Sharma"},
        status:"in-progress",
        upvotes:["u2","u3","u4"],
        comments:[
            {
                _id:"c1",
                author:{_id:"u4",name:"Kabir Singh"},
                text:"Same problem in our department. Seniors would also like to mentor teams.",
                createdAt:"2026-08-02T11:20:00.000Z"
            },
            {
                _id:"c2",
                author:{_id:"u3",name:"Neha Verma"},
                text:"Should teams be matched by skills, or should students just browse profiles?",
                createdAt:"2026-08-03T09:05:00.000Z"
            }
        ],
        solutions:[
            {
                _id:"s1",
                author:{_id:"u2",name:"Arjun Mehta"},
                title:"TeamUp - skill based teammate finder",
                description:"Students create a profile with their skills and interests, post project ideas and send join requests. Filters help find people with missing skills like design or backend.",
                repoUrl:"https://github.com/example/teamup",
                techStack:["React","Node.js","MongoDB"],
                createdAt:"2026-08-05T16:40:00.000Z"
            }
        ],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-08-01T10:00:00.000Z",
        updatedAt:"2026-08-05T16:40:00.000Z"
    },
    {
        _id:"p2",
        title:"No single place to find campus events and workshops",
        description:"Club events, workshops and seminars are announced in different WhatsApp groups and notice boards. Students regularly miss useful events because they are not in the right group or see the notice too late.",
        category:"Events",
        outcome:"One reliable calendar with filters and reminders for campus activities.",
        tags:["events","clubs","notifications"],
        author:{_id:"u4",name:"Kabir Singh"},
        status:"open",
        upvotes:["u1","u3"],
        comments:[
            {
                _id:"c3",
                author:{_id:"u1",name:"Riya Sharma"},
                text:"A weekly calendar view would already help a lot.",
                createdAt:"2026-08-10T13:00:00.000Z"
            }
        ],
        solutions:[],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-08-09T08:30:00.000Z",
        updatedAt:"2026-08-10T13:00:00.000Z"
    },
    {
        _id:"p3",
        title:"College bus timings are unpredictable",
        description:"The college bus from the city often leaves earlier or later than the printed timetable. Students wait at the stop for a long time without knowing whether the bus has already left or is stuck in traffic.",
        category:"Transport",
        outcome:"A simple live view of the last known bus stop and an indicative arrival time.",
        paid:true,
        budget:"₹8,000–₹20,000",
        tags:["bus","commute","tracking"],
        author:{_id:"u4",name:"Kabir Singh"},
        status:"open",
        upvotes:["u1","u2","u3"],
        comments:[],
        solutions:[
            {
                _id:"s2",
                author:{_id:"u3",name:"Neha Verma"},
                title:"Live bus status board",
                description:"The bus conductor taps a button in a simple web app at each stop. Students see the last stop reached and an estimated arrival time.",
                repoUrl:"",
                techStack:["React","Express"],
                createdAt:"2026-08-20T18:10:00.000Z"
            }
        ],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-08-15T07:50:00.000Z",
        updatedAt:"2026-08-20T18:10:00.000Z"
    },
    {
        _id:"p4",
        title:"Seniors' books and notes go to waste every year",
        description:"Final year students throw away or sell textbooks and handwritten notes as scrap, while juniors buy the same books new. There is no simple way for seniors to give or lend their study material to juniors.",
        category:"Resources",
        tags:["books","notes","sharing"],
        author:{_id:"u1",name:"Riya Sharma"},
        status:"open",
        upvotes:["u4"],
        comments:[],
        solutions:[],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-08-22T12:00:00.000Z",
        updatedAt:"2026-08-22T12:00:00.000Z"
    },
    {
        _id:"p5",
        title:"Broken classroom projectors take weeks to get repaired",
        description:"When a projector or fan stops working, students tell the class teacher, who tells the department, and the complaint often gets lost. Nobody knows whether the issue was reported or when it will be fixed.",
        category:"Facilities",
        tags:["maintenance","complaints","classrooms"],
        author:{_id:"u1",name:"Riya Sharma"},
        status:"solved",
        upvotes:["u2","u4"],
        comments:[
            {
                _id:"c4",
                author:{_id:"u2",name:"Arjun Mehta"},
                text:"A QR code on each room linking to a complaint form could work well.",
                createdAt:"2026-09-02T10:30:00.000Z"
            }
        ],
        solutions:[
            {
                _id:"s3",
                author:{_id:"u2",name:"Arjun Mehta"},
                title:"FixIt - QR based facility complaints",
                description:"Each classroom gets a QR code. Scanning it opens a short form, and the maintenance team gets a dashboard showing pending and fixed complaints for every room.",
                repoUrl:"https://github.com/example/fixit",
                techStack:["React","Node.js","MongoDB"],
                createdAt:"2026-09-05T15:00:00.000Z"
            }
        ],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-09-01T09:00:00.000Z",
        updatedAt:"2026-09-05T15:00:00.000Z"
    },
    {
        _id:"p6",
        title:"Hostel laundry machines are always occupied",
        description:"Our hostel has only four washing machines for two hundred students. There is no booking system, so students carry their clothes up and down several times hoping a machine is free.",
        category:"Campus Life",
        outcome:"Let residents reserve a laundry slot and see when machines are available.",
        tags:["hostel","laundry","booking"],
        author:{_id:"u4",name:"Kabir Singh"},
        status:"open",
        upvotes:["u1"],
        comments:[],
        solutions:[],
        similarProblems:[],
        embeddingStatus:"not-processed",
        createdAt:"2026-09-12T19:30:00.000Z",
        updatedAt:"2026-09-12T19:30:00.000Z"
    },
    {
        _id:"p7",
        title:"Campus event announcements are scattered across group chats",
        description:"Students hear about useful workshops and club events through different messaging groups, posters, and forwarded notices. It is hard to know what is happening this week or find the details again after an announcement disappears in chat.",
        category:"Events",
        outcome:"A searchable, up-to-date calendar for campus events with clear time, location, and organizer details.",
        constraints:"Organizers should be able to post updates quickly, and students should not need to join every club chat.",
        tags:["events","clubs","calendar"],
        author:{_id:"u3",name:"Neha Verma"},
        status:"open",
        upvotes:["u1","u2"],
        comments:[],
        solutions:[],
        similarProblems:["p2"],
        createdAt:"2026-09-18T11:20:00.000Z",
        updatedAt:"2026-09-18T11:20:00.000Z"
    }
];
