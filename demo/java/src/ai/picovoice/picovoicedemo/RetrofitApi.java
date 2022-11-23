package ai.picovoice.picovoicedemo;

import java.util.Map;

import retrofit2.Call;
import retrofit2.http.*;

public interface RetrofitApi {
    @Headers({
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZjQ1MjUzMGRmOTc0MmM5YTQzZTYxNDcwOGZiY2U0MiIsImlhdCI6MTY2OTEzOTc1NywiZXhwIjoxOTg0NDk5NzU3fQ.i05deYebPb6JfRQTVdAKFdnGFEtV1EL3ifK_Vqcm3YQ",
        "content-type: application/json"
    })
    @POST("api/events/rhasspy_{event}")
    Call<Void> sendEvent(
        @Path("event") String event,
        @Body Map<String, String> slots
    );


    @POST("http://192.168.1.128:12101/api/text-to-speech")
    Call<Void> sendWakeWord(
        @Body String text
    );
}
