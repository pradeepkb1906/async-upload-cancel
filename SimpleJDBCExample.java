import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public class SimpleJDBCExample {
    public static void main(String[] args) {
        String jdbcURL = "jdbc:mysql://localhost:3306/demo_db";
        String username = "root";
        String password = "password";

        try {
            Connection connection = DriverManager.getConnection(jdbcURL, username, password);
            Statement statement = connection.createStatement();
            ResultSet result = statement.executeQuery("SELECT * FROM users");

            while (result.next()) {
                System.out.println("ID: " + result.getInt("id") + ", Name: " + result.getString("name"));
            }

            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
